import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader
import chromadb
from chromadb.config import Settings
import hashlib
import pdfplumber

# Load environment variables
load_dotenv()

# Fix PyTorch device issues
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()

class PDFProcessor:
    def __init__(self, chroma_db_path: str = "chroma_db"):
        """Initialize the PDF processor with necessary components"""
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.2  # Lower temperature for more factual answers
        )
        
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize the embeddings (meta tensor bug fix: do not pass device kwargs)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB client with configurable path
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_db_path
        )
        
        self.knowledge_bases = {}  # Dictionary to store filename -> collection_name mapping
        self.pdf_tables = {}  # Dictionary to store filename -> list of table rows
    
    def _create_valid_collection_name(self, filename: str) -> str:
        """Create a valid collection name from filename"""
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Create a hash of the full filename to ensure uniqueness
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        
        # Take first 20 characters of the name for readability
        name = name[:20]
        
        # Replace spaces and special characters with underscores
        name = ''.join(c if c.isalnum() else '_' for c in name)
        
        # Ensure name starts and ends with alphanumeric
        name = name.strip('_')
        
        # Remove consecutive underscores
        while '__' in name:
            name = name.replace('__', '_')
        
        # Ensure minimum length
        if len(name) < 3:
            name = 'pdf_' + name
        
        # Combine name and hash to create unique collection name
        collection_name = f"pdf_{name}_{file_hash}"
        
        # Ensure total length is within limits
        if len(collection_name) > 63:
            collection_name = collection_name[:55] + '_' + file_hash
        
        return collection_name
    
    def process_pdf(self, file_path: str) -> str:
        """Process a PDF file and store its content in ChromaDB. Also extract tables."""
        try:
            # Read PDF file (text extraction)
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Extract tables using pdfplumber
            table_rows = []
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                # Convert all cells to strings and strip whitespace
                                clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
                                table_rows.append(clean_row)
            except Exception as e:
                print(f"[WARNING] Table extraction failed for {file_path}: {e}")
            self.pdf_tables[file_path] = table_rows
            
            # Create a valid collection name
            collection_name = self._create_valid_collection_name(os.path.basename(file_path))
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create or get collection
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"source": file_path}
            )
            
            # Add documents to collection
            collection.add(
                documents=chunks,
                ids=[f"{collection_name}_{i}" for i in range(len(chunks))]
            )
            
            # Store mapping
            self.knowledge_bases[file_path] = collection_name
            
            return collection_name
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def search_multiple_pdfs(self, query: str) -> Dict[str, Any]:
        """Search across all PDF collections for an answer"""
        try:
            all_results = []
            result_sources = []  # Track which collection each result came from
            result_distances = []  # Track the distance (similarity) for each chunk
            total_sources_checked = 0
            
            # Search in each collection
            for file_path, collection_name in self.knowledge_bases.items():
                collection = self.chroma_client.get_collection(collection_name)
                results = collection.query(
                    query_texts=[query],
                    n_results=3
                )
                if results and results['documents'] and results['documents'][0]:
                    docs = results['documents'][0]
                    dists = results.get('distances', [[None]*len(docs)])[0]
                    for doc, dist in zip(docs, dists):
                        all_results.append(doc)
                        result_sources.append(file_path)
                        result_distances.append(dist)
                total_sources_checked += 1
            
            if not all_results:
                return {
                    "answer": "I couldn't find any relevant information in the documents.",
                    "source": "general_knowledge",
                    "confidence": 0.0
                }
            
            # Find the most relevant chunk (lowest distance)
            min_idx = None
            if result_distances and any(d is not None for d in result_distances):
                min_dist = float('inf')
                for idx, dist in enumerate(result_distances):
                    if dist is not None and dist < min_dist:
                        min_dist = dist
                        min_idx = idx
            else:
                min_idx = 0  # fallback to first if no distances
            top_source = result_sources[min_idx] if min_idx is not None else None
            top_pdf = os.path.basename(top_source) if top_source else None
            
            # Use all results as context for the LLM
            combined_context = "\n".join(all_results)
            prompt = f"""Based on the following information from multiple documents, please provide a comprehensive answer to the question. If the information is not sufficient, say so.\n\nQuestion: {query}\n\nInformation from documents:\n{combined_context}\n\nAnswer:"""
            # --- DEBUG LOGGING ---
            print("\n[DEBUG] Prompt sent to LLM:\n", prompt[:1000], "...\n[END PROMPT]\n")
            print("[DEBUG] Top 3 retrieved chunks:")
            for i, chunk in enumerate(all_results[:3]):
                print(f"Chunk {i+1}:\n{chunk[:500]}\n---")
            # --- END DEBUG LOGGING ---
            response = self.llm.invoke(prompt)
            
            # Compute confidence based on the most relevant chunk's distance
            if result_distances and any(d is not None for d in result_distances):
                min_dist = min([d for d in result_distances if d is not None])
                confidence = max(0.0, min(1.0, 1.0 - min_dist))
            else:
                confidence = 0.0
            
            return {
                "answer": response.content,
                "source": top_pdf or "multiple_documents",
                "confidence": confidence,
                "details": {
                    "sources": [top_pdf] if top_pdf else [],
                    "total_sources_checked": total_sources_checked
                }
            }
        except Exception as e:
            raise Exception(f"Error searching PDFs: {str(e)}")
    
    def delete_pdf(self, file_path: str) -> bool:
        """Delete a PDF's collection from ChromaDB"""
        try:
            if file_path in self.knowledge_bases:
                collection_name = self.knowledge_bases[file_path]
                self.chroma_client.delete_collection(collection_name)
                del self.knowledge_bases[file_path]
                return True
            return False
        except Exception as e:
            raise Exception(f"Error deleting PDF: {str(e)}")
    
    def cleanup_collections(self) -> int:
        """Clean up orphaned collections"""
        try:
            # Get all collections
            collections = self.chroma_client.list_collections()
            collection_names = {c.name for c in collections}
            
            # Find orphaned collections
            active_collections = set(self.knowledge_bases.values())
            orphaned_collections = collection_names - active_collections
            
            # Delete orphaned collections
            for collection_name in orphaned_collections:
                self.chroma_client.delete_collection(collection_name)
            
            return len(orphaned_collections)
        except Exception as e:
            raise Exception(f"Error cleaning up collections: {str(e)}")
    
    def search_pdf(self, identifier: str, query: str) -> Dict[str, Any]:
        """Search a specific PDF collection by filename or collection id for an answer"""
        try:
            # Log available identifiers for debugging
            print("[DEBUG] knowledge_bases keys:", list(self.knowledge_bases.keys()))
            print("[DEBUG] knowledge_bases values:", list(self.knowledge_bases.values()))
            print("[DEBUG] identifier received:", identifier)
            
            # Normalize identifier for matching
            norm_id = identifier.strip().lower()
            collection_name = None
            # Try exact match to filename (full path)
            for fname, cname in self.knowledge_bases.items():
                if fname == identifier or fname.lower() == norm_id:
                    collection_name = cname
                    break
            # Try match to collection name
            if not collection_name:
                for cname in self.knowledge_bases.values():
                    if cname == identifier or cname.lower() == norm_id:
                        collection_name = cname
                        break
            # Try basename match (case-insensitive)
            if not collection_name:
                for fname, cname in self.knowledge_bases.items():
                    if os.path.basename(fname) == identifier or os.path.basename(fname).lower() == norm_id:
                        collection_name = cname
                        break
            # Try basename without extension
            if not collection_name:
                for fname, cname in self.knowledge_bases.items():
                    base = os.path.splitext(os.path.basename(fname))[0]
                    if base == identifier or base.lower() == norm_id:
                        collection_name = cname
                        break
            if not collection_name:
                raise Exception(f"No collection found for identifier: {identifier}")

            print(f"[DEBUG] Matched collection_name: {collection_name}")
            collection = self.chroma_client.get_collection(collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            if not results or not results['documents'] or not results['documents'][0]:
                return {
                    "answer": "I couldn't find any relevant information in the document.",
                    "source": collection_name,
                    "confidence": 0.0
                }
            # Combine results and get answer from LLM
            combined_context = "\n".join(results['documents'][0])
            prompt = f"""Based on the following information from the document, please answer the question. If the information is not sufficient, say so.\n\nQuestion: {query}\n\nInformation from document:\n{combined_context}\n\nAnswer:"""
            response = self.llm.invoke(prompt)
            return {
                "answer": response.content,
                "source": collection_name,
                "confidence": 0.8
            }
        except Exception as e:
            raise Exception(f"Error searching PDF: {str(e)}")
