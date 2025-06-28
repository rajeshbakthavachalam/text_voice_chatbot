import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from app.logic.pdf_processor import PDFProcessor
import chromadb
from chromadb.config import Settings
import numpy as np
from datetime import datetime
import pandas as pd
from logic.file_extractor import extract_text_from_file

class KnowledgeBaseManager:
    def __init__(self, documents_directory: str = "pdfs", db_directory: str = "chroma_db", search_type: str = "similarity", search_kwargs: dict = None):
        """
        Initialize the knowledge base manager
        
        Args:
            documents_directory: Directory containing document files (PDF, DOCX, CSV, TXT, RAR, ZIP)
            db_directory: Directory for ChromaDB storage
            search_type: Retrieval mechanism to use ("similarity", "mmr", "similarity_score_threshold")
            search_kwargs: Additional search parameters (e.g., {"k": 3, ...})
        """
        self.documents_directory = Path(documents_directory)
        self.db_directory = Path(db_directory)
        self.db_directory.mkdir(exist_ok=True)
        
        # Supported file extensions
        self.supported_extensions = {'.pdf', '.docx', '.csv', '.txt', '.rar', '.zip', '.xlsx', '.json'}
        
        # Initialize ChromaDB client with unique settings
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_directory)
        )
        
        # --- Retrieval config ---
        self.search_type = search_type or "similarity"
        self.search_kwargs = search_kwargs or {"k": 3}
        
        # Initialize PDF processor with our ChromaDB client and retrieval config
        self.pdf_processor = PDFProcessor(
            chroma_db_path=str(self.db_directory)
        )
        self.pdf_processor.chroma_client = self.chroma_client
        
        # Load or create knowledge base index
        self.index_file = self.db_directory / "knowledge_base_index.json"
        self.knowledge_base_index = self._load_index()

        # --- NEW: Load collections into PDFProcessor's in-memory knowledge_bases ---
        for file_name, info in self.knowledge_base_index.get("documents", {}).items():
            collection_name = info.get("collection_name")
            if collection_name:
                self.pdf_processor.knowledge_bases[file_name] = collection_name
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the knowledge base index from file"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)
                
                # Handle backward compatibility: convert old "pdfs" structure to "documents"
                if "pdfs" in index_data and "documents" not in index_data:
                    print("Converting old index structure from 'pdfs' to 'documents'...")
                    index_data["documents"] = index_data.pop("pdfs")
                
                # Ensure the required keys exist
                if "documents" not in index_data:
                    index_data["documents"] = {}
                if "collections" not in index_data:
                    index_data["collections"] = {}
                
                return index_data
            except Exception as e:
                print(f"Error loading index: {e}")
                return {"documents": {}, "collections": {}}
        return {"documents": {}, "collections": {}}
    
    def _save_index(self):
        """Save the knowledge base index to file"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.knowledge_base_index, f, indent=2)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def get_document_files(self) -> List[str]:
        """Get list of supported document files in the documents directory"""
        document_files = []
        if self.documents_directory.exists():
            for file in self.documents_directory.iterdir():
                if file.is_file() and file.suffix.lower() in self.supported_extensions:
                    document_files.append(file.name)
        return sorted(document_files)
    
    def is_document_indexed(self, file_name: str) -> bool:
        """Check if a document is already indexed"""
        return file_name in self.knowledge_base_index["documents"]
    
    def get_indexed_documents(self) -> List[str]:
        """Get list of indexed documents"""
        return list(self.knowledge_base_index["documents"].keys())
    
    def get_document_info(self, file_name: str) -> Dict[str, Any]:
        """Get information about a document"""
        if self.is_document_indexed(file_name):
            return self.knowledge_base_index["documents"][file_name]
        return {}
    
    def index_document(self, file_name: str) -> bool:
        """Index a single document file"""
        try:
            file_path = self.documents_directory / file_name
            if not file_path.exists():
                print(f"Document file not found: {file_path}")
                return False
            
            # Check if file type is supported
            if file_path.suffix.lower() not in self.supported_extensions:
                print(f"Unsupported file type: {file_path.suffix}")
                return False
            
            # Handle PDF files using PDFProcessor (which now uses simple text splitting)
            if file_path.suffix.lower() == '.pdf':
                collection_name = self.pdf_processor.process_pdf(str(file_path))
                # Get file size and text length for PDF
                file_size = file_path.stat().st_size
                # For PDFs, we'll estimate text length (PDFProcessor doesn't return it)
                text_length = file_size // 10  # Rough estimate
            else:
                # Handle non-PDF files using simple text splitting
                print(f"[INFO] Processing {file_name} with simple text splitting")
                extracted_text = extract_text_from_file(str(file_path))
                
                if not extracted_text or extracted_text.strip() == "":
                    print(f"No text could be extracted from: {file_name}")
                    return False
                
                # Create a valid collection name
                collection_name = self._create_valid_collection_name(file_name)
                
                # Use simple text splitting (the working approach)
                print(f"[INFO] Using simple text splitting for {file_name}")
                chunks = self.pdf_processor.text_splitter.split_text(extracted_text)
                print(f"[INFO] Created {len(chunks)} chunks using simple text splitting for {file_name}")
                
                # Create or get collection
                collection = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"source": str(file_path)}
                )
                
                # Add documents to collection
                collection.add(
                    documents=chunks,
                    ids=[f"{collection_name}_{i}" for i in range(len(chunks))]
                )
                
                file_size = file_path.stat().st_size
                text_length = len(extracted_text)
            
            # Store mapping in PDFProcessor's knowledge_bases for compatibility
            # Use the full file path as key to match PDFProcessor's expectation
            self.pdf_processor.knowledge_bases[str(file_path)] = collection_name
            
            # Update index
            self.knowledge_base_index["documents"][file_name] = {
                "collection_name": collection_name,
                "file_path": str(file_path),
                "indexed_at": str(file_path.stat().st_mtime),
                "file_type": file_path.suffix[1:].lower(),
                "file_name": file_path.name,
                "file_size": file_size,
                "text_length": text_length,
                "chunking_method": "simple_text_splitting"  # Track the chunking method used
            }
            self.knowledge_base_index["collections"][collection_name] = file_name
            
            # Save index
            self._save_index()
            
            print(f"Successfully indexed: {file_name} ({file_path.suffix}) with simple text splitting")
            return True
            
        except Exception as e:
            print(f"Error indexing {file_name}: {e}")
            return False
    
    def _create_valid_collection_name(self, filename: str) -> str:
        """Create a valid collection name from filename"""
        import hashlib
        
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
            name = 'doc_' + name
        
        # Combine name and hash to create unique collection name
        collection_name = f"doc_{name}_{file_hash}"
        
        # Ensure total length is within limits
        if len(collection_name) > 63:
            collection_name = collection_name[:55] + '_' + file_hash
        
        return collection_name
    
    def index_all_documents(self) -> Dict[str, bool]:
        """Index all supported document files in the directory"""
        document_files = self.get_document_files()
        results = {}
        
        print(f"Found {len(document_files)} document files to index")
        
        for file_name in document_files:
            if self.is_document_indexed(file_name):
                print(f"Skipping {file_name} (already indexed)")
                results[file_name] = True
            else:
                print(f"Indexing {file_name}...")
                results[file_name] = self.index_document(file_name)
        
        return results
    
    def search_single_document(self, file_name: str, question: str) -> Dict[str, Any]:
        """Search in a specific document"""
        # Always reload index and mapping to include new documents
        self.knowledge_base_index = self._load_index()
        
        # Map filenames to full paths for PDFProcessor's knowledge_bases
        self.pdf_processor.knowledge_bases = {}
        for doc_name, info in self.knowledge_base_index["documents"].items():
            full_path = str(self.documents_directory / doc_name)
            self.pdf_processor.knowledge_bases[full_path] = info["collection_name"]
        
        if not self.is_document_indexed(file_name):
            return {
                "error": f"Document '{file_name}' is not indexed. Please index it first.",
                "answer": None,
                "source": None,
                "confidence": 0.0
            }
        try:
            collection_name = self.knowledge_base_index["documents"][file_name]["collection_name"]
            result = self.pdf_processor.search_pdf(collection_name, question)
            
            # Preserve the source information from the PDF processor
            # Only add file_type and file_name if they're not already present
            if "file_type" not in result:
                result["file_type"] = self.knowledge_base_index["documents"][file_name].get("file_type", "unknown")
            if "file_name" not in result:
                result["file_name"] = file_name
            
            return result
        except Exception as e:
            return {
                "error": f"Error searching document '{file_name}': {str(e)}",
                "answer": None,
                "source": None,
                "confidence": 0.0
            }
    
    def search_all_documents(self, question: str) -> Dict[str, Any]:
        """Search across all indexed documents"""
        # Always reload index and mapping to include new documents
        self.knowledge_base_index = self._load_index()
        
        # Map filenames to full paths for PDFProcessor's knowledge_bases
        self.pdf_processor.knowledge_bases = {}
        for file_name, info in self.knowledge_base_index["documents"].items():
            full_path = str(self.documents_directory / file_name)
            self.pdf_processor.knowledge_bases[full_path] = info["collection_name"]
        
        indexed_documents = self.get_indexed_documents()
        if not indexed_documents:
            return {
                "error": "No documents are indexed. Please index some documents first.",
                "answer": None,
                "source": None,
                "confidence": 0.0
            }
        try:
            # Use the existing search_multiple_pdfs method (it works with any text)
            result = self.pdf_processor.search_multiple_pdfs(question)
            result["indexed_documents"] = indexed_documents
            
            # Preserve the source information from the PDF processor
            # Only add file_type and file_name if they're not already present
            if "file_type" not in result:
                first_document = indexed_documents[0]
                result["file_type"] = self.knowledge_base_index["documents"][first_document].get("file_type", "unknown")
            if "file_name" not in result:
                first_document = indexed_documents[0]
                result["file_name"] = self.knowledge_base_index["documents"][first_document].get("file_name", first_document)
            
            return result
        except Exception as e:
            return {
                "error": f"Error searching documents: {str(e)}",
                "answer": None,
                "source": None,
                "confidence": 0.0
            }
    
    def remove_document(self, file_name: str) -> bool:
        """Remove a document from the knowledge base"""
        if not self.is_document_indexed(file_name):
            return False
        
        try:
            collection_name = self.knowledge_base_index["documents"][file_name]["collection_name"]
            
            # Delete collection from ChromaDB
            self.chroma_client.delete_collection(collection_name)
            
            # Remove from index
            del self.knowledge_base_index["documents"][file_name]
            del self.knowledge_base_index["collections"][collection_name]
            
            # Save index
            self._save_index()
            
            print(f"Successfully removed: {file_name}")
            return True
            
        except Exception as e:
            print(f"Error removing {file_name}: {e}")
            return False
    
    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """Get the current status of the knowledge base"""
        all_files = self.get_document_files()
        indexed_files = self.get_indexed_documents()
        pending_files = [f for f in all_files if f not in indexed_files]
        
        return {
            "total_documents": len(all_files),
            "indexed_documents": len(indexed_files),
            "pending_documents": pending_files,
            "indexed_documents_list": indexed_files,
            "pending_documents_list": pending_files,
            "supported_extensions": list(self.supported_extensions)
        }
    
    def rebuild_index(self) -> Dict[str, bool]:
        """Rebuild the entire knowledge base index"""
        try:
            # Clear all collections
            collections = self.chroma_client.list_collections()
            for collection in collections:
                self.chroma_client.delete_collection(collection.name)
            
            # Clear index
            self.knowledge_base_index = {"documents": {}, "collections": {}}
            self._save_index()
            
            # Re-index all documents
            return self.index_all_documents()
            
        except Exception as e:
            print(f"Error rebuilding index: {e}")
            return {}
    
    def auto_index_new_files(self) -> Dict[str, bool]:
        """Automatically index any new files that have been added to the directory"""
        all_files = self.get_document_files()
        results = {}
        
        for file_name in all_files:
            if not self.is_document_indexed(file_name):
                print(f"Auto-indexing new file: {file_name}")
                results[file_name] = self.index_document(file_name)
        
        return results
    
    # ==================== EVALUATION METRICS METHODS ====================
    
    def calculate_search_metrics(self, query: str, expected_answer: str, actual_answer: str, 
                               expected_sources: List[str] = None, actual_sources: List[str] = None) -> Dict[str, float]:
        """
        Calculate evaluation metrics for a single search query
        
        Args:
            query: The search query
            expected_answer: Expected/ground truth answer
            actual_answer: Actual answer from the system
            expected_sources: Expected source PDFs
            actual_sources: Actual source PDFs returned
            
        Returns:
            Dictionary containing various metrics
        """
        metrics = {}
        
        # Answer relevance metrics (using simple text similarity)
        answer_similarity = self._calculate_text_similarity(expected_answer.lower(), actual_answer.lower())
        metrics['answer_relevance'] = answer_similarity
        
        # Source accuracy metrics
        if expected_sources and actual_sources:
            source_precision = len(set(expected_sources) & set(actual_sources)) / len(actual_sources) if actual_sources else 0
            source_recall = len(set(expected_sources) & set(actual_sources)) / len(expected_sources) if expected_sources else 0
            source_f1 = 2 * (source_precision * source_recall) / (source_precision + source_recall) if (source_precision + source_recall) > 0 else 0
            
            metrics['source_precision'] = source_precision
            metrics['source_recall'] = source_recall
            metrics['source_f1'] = source_f1
            metrics['source_accuracy'] = len(set(expected_sources) & set(actual_sources)) / len(set(expected_sources) | set(actual_sources)) if (expected_sources or actual_sources) else 0
        
        # Answer length metrics
        expected_length = len(expected_answer.split())
        actual_length = len(actual_answer.split())
        metrics['length_ratio'] = actual_length / expected_length if expected_length > 0 else 0
        
        # Keyword coverage
        expected_keywords = set(expected_answer.lower().split())
        actual_keywords = set(actual_answer.lower().split())
        keyword_coverage = len(expected_keywords & actual_keywords) / len(expected_keywords) if expected_keywords else 0
        metrics['keyword_coverage'] = keyword_coverage
        
        return metrics
    
    def evaluate_search_performance(self, test_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate search performance on a set of test queries
        
        Args:
            test_queries: List of dictionaries with keys:
                - 'query': The search query
                - 'expected_answer': Expected answer
                - 'expected_sources': Expected source PDFs (optional)
                - 'pdf_name': Specific PDF to search (optional, for single PDF search)
                
        Returns:
            Dictionary containing aggregated metrics
        """
        all_metrics = []
        single_pdf_metrics = []
        multi_pdf_metrics = []
        
        for test_case in test_queries:
            query = test_case['query']
            expected_answer = test_case['expected_answer']
            expected_sources = test_case.get('expected_sources', [])
            pdf_name = test_case.get('pdf_name')
            
            # Perform search
            if pdf_name:
                result = self.search_single_pdf(pdf_name, query)
                search_type = 'single_pdf'
            else:
                result = self.search_all_pdfs(query)
                search_type = 'multi_pdf'
            
            if 'error' in result and result['error']:
                continue  # Skip failed searches
            
            actual_answer = result.get('answer', '')
            actual_sources = result.get('sources', [])
            
            # Calculate metrics
            metrics = self.calculate_search_metrics(
                query, expected_answer, actual_answer, 
                expected_sources, actual_sources
            )
            
            # Add metadata
            metrics['query'] = query
            metrics['search_type'] = search_type
            metrics['pdf_name'] = pdf_name
            metrics['confidence'] = result.get('confidence', 0.0)
            metrics['timestamp'] = datetime.now().isoformat()
            
            all_metrics.append(metrics)
            
            if search_type == 'single_pdf':
                single_pdf_metrics.append(metrics)
            else:
                multi_pdf_metrics.append(metrics)
        
        # Aggregate metrics
        return self._aggregate_metrics(all_metrics, single_pdf_metrics, multi_pdf_metrics)
    
    def _aggregate_metrics(self, all_metrics: List[Dict], single_pdf_metrics: List[Dict], 
                          multi_pdf_metrics: List[Dict]) -> Dict[str, Any]:
        """Aggregate metrics across all test cases"""
        
        def calculate_aggregate(metric_list, metric_name):
            if not metric_list:
                return 0.0
            values = [m.get(metric_name, 0.0) for m in metric_list if m.get(metric_name) is not None]
            return np.mean(values) if values else 0.0
        
        def calculate_std(metric_list, metric_name):
            if not metric_list:
                return 0.0
            values = [m.get(metric_name, 0.0) for m in metric_list if m.get(metric_name) is not None]
            return np.std(values) if values else 0.0
        
        # Overall metrics
        overall_metrics = {
            'total_queries': len(all_metrics),
            'single_pdf_queries': len(single_pdf_metrics),
            'multi_pdf_queries': len(multi_pdf_metrics),
            'answer_relevance_mean': calculate_aggregate(all_metrics, 'answer_relevance'),
            'answer_relevance_std': calculate_std(all_metrics, 'answer_relevance'),
            'keyword_coverage_mean': calculate_aggregate(all_metrics, 'keyword_coverage'),
            'keyword_coverage_std': calculate_std(all_metrics, 'keyword_coverage'),
            'length_ratio_mean': calculate_aggregate(all_metrics, 'length_ratio'),
            'length_ratio_std': calculate_std(all_metrics, 'length_ratio'),
            'confidence_mean': calculate_aggregate(all_metrics, 'confidence'),
            'confidence_std': calculate_std(all_metrics, 'confidence'),
        }
        
        # Source metrics (if available)
        source_metrics = [m for m in all_metrics if 'source_precision' in m]
        if source_metrics:
            overall_metrics.update({
                'source_precision_mean': calculate_aggregate(source_metrics, 'source_precision'),
                'source_precision_std': calculate_std(source_metrics, 'source_precision'),
                'source_recall_mean': calculate_aggregate(source_metrics, 'source_recall'),
                'source_recall_std': calculate_std(source_metrics, 'source_recall'),
                'source_f1_mean': calculate_aggregate(source_metrics, 'source_f1'),
                'source_f1_std': calculate_std(source_metrics, 'source_f1'),
                'source_accuracy_mean': calculate_aggregate(source_metrics, 'source_accuracy'),
                'source_accuracy_std': calculate_std(source_metrics, 'source_accuracy'),
            })
        
        # Single PDF specific metrics
        if single_pdf_metrics:
            overall_metrics['single_pdf'] = {
                'answer_relevance_mean': calculate_aggregate(single_pdf_metrics, 'answer_relevance'),
                'keyword_coverage_mean': calculate_aggregate(single_pdf_metrics, 'keyword_coverage'),
                'confidence_mean': calculate_aggregate(single_pdf_metrics, 'confidence'),
            }
        
        # Multi PDF specific metrics
        if multi_pdf_metrics:
            overall_metrics['multi_pdf'] = {
                'answer_relevance_mean': calculate_aggregate(multi_pdf_metrics, 'answer_relevance'),
                'keyword_coverage_mean': calculate_aggregate(multi_pdf_metrics, 'keyword_coverage'),
                'confidence_mean': calculate_aggregate(multi_pdf_metrics, 'confidence'),
            }
        
        return {
            'summary': overall_metrics,
            'detailed_results': all_metrics,
            'evaluation_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity using word overlap"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def save_evaluation_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save evaluation results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_results_{timestamp}.json"
        
        filepath = self.db_directory / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            return str(filepath)
        except Exception as e:
            print(f"Error saving evaluation results: {e}")
            return None
    
    def load_evaluation_results(self, filename: str) -> Dict[str, Any]:
        """Load evaluation results from a JSON file"""
        filepath = self.db_directory / filename
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading evaluation results: {e}")
            return None
    
    def get_evaluation_history(self) -> List[str]:
        """Get list of available evaluation result files"""
        evaluation_files = []
        for file in self.db_directory.glob("evaluation_results_*.json"):
            evaluation_files.append(file.name)
        return sorted(evaluation_files, reverse=True)
    
    def create_sample_test_queries(self) -> List[Dict[str, Any]]:
        """Create sample test queries for evaluation"""
        sample_queries = [
            {
                'query': 'What are the insurance benefits?',
                'expected_answer': 'The insurance provides coverage for medical expenses including hospitalization, outpatient treatment, and prescription drugs.',
                'expected_sources': ['mediclaim.pdf', '2022 Insurance Benefit Manual.pdf'],
                'search_type': 'multi_pdf'
            },
            {
                'query': 'What is the coverage limit?',
                'expected_answer': 'The coverage limit varies by plan type and can range from 1 lakh to 10 lakhs.',
                'expected_sources': ['mediclaim.pdf'],
                'search_type': 'single_pdf',
                'pdf_name': 'mediclaim.pdf'
            },
            {
                'query': 'What expenses are not covered?',
                'expected_answer': 'Expenses not covered include cosmetic procedures, pre-existing conditions, and experimental treatments.',
                'expected_sources': ['NonPayableChanges.pdf'],
                'search_type': 'single_pdf',
                'pdf_name': 'NonPayableChanges.pdf'
            }
        ]
        return sample_queries
    
    def index_file(self, file_name: str) -> bool:
        """Index a single non-PDF file (docx, xlsx, txt, json, zip, rar, csv)"""
        try:
            file_path = self.pdf_directory / file_name
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return False

            # Extract text from the file
            extracted_text = extract_text_from_file(str(file_path))
            # Use file name as collection name (or customize as needed)
            collection_name = f"{file_path.stem}_collection"
            # Add to ChromaDB (simulate PDFProcessor behavior)
            self.chroma_client.get_or_create_collection(collection_name)
            # Store the extracted text as a document in the collection
            self.chroma_client.get_collection(collection_name).add(
                documents=[extracted_text],
                metadatas=[{"file_name": file_name, "file_type": file_path.suffix[1:]}],
                ids=[file_name]
            )
            # Update index
            self.knowledge_base_index["pdfs"][file_name] = {
                "collection_name": collection_name,
                "file_path": str(file_path),
                "indexed_at": str(file_path.stat().st_mtime),
                "file_type": file_path.suffix[1:],
                "file_name": file_path.name
            }
            self.knowledge_base_index["collections"][collection_name] = file_name
            # Save index
            self._save_index()
            print(f"Successfully indexed: {file_name}")
            return True
        except Exception as e:
            print(f"Error indexing {file_name}: {e}")
            return False 