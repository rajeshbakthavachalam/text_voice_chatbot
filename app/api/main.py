from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from typing import List, Optional
from urllib.parse import quote
from pydub import AudioSegment
import uuid
import time
from pydub.utils import mediainfo

from app.logic.pdf_processor import PDFProcessor
from app.logic.audio_processor import AudioProcessor

# Initialize FastAPI app with metadata
app = FastAPI(
    title="PDF Question Answering API",
    description="""
    A powerful API for uploading, managing, and querying PDF documents.
    Features include:
    - PDF upload and management
    - Semantic search across multiple documents
    - Question answering with source attribution
    - Voice search capabilities
    - Insurance policy management
    """,
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
pdf_processor = PDFProcessor()
audio_processor = AudioProcessor()

# Create uploads directory if it doesn't exist
UPLOADS_DIR = r"C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\text_voice_chatbot\pdfs"
os.makedirs(UPLOADS_DIR, exist_ok=True)

def ensure_pcm_wav(input_path, output_path=None):
    if output_path is None:
        output_path = input_path
    try:
        # This helps debug any format issues
        print("Audio file info:", mediainfo(input_path))
        
        # Explicitly specify format as 'wav'
        audio = AudioSegment.from_file(input_path, format="wav")
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(output_path, format="wav")
    except Exception as e:
        print(f"[Audio Error] Could not decode file: {e}")
        raise

def safe_delete(path, retries=20, delay=0.25):
    for _ in range(retries):
        try:
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception:
            time.sleep(delay)
    print(f"Could not delete temp file after retries: {path}")
    return False

@app.post("/upload/pdf", 
    summary="Upload a PDF file",
    description="Upload a PDF file to be processed and added to the knowledge base.",
    response_description="Returns the filename and processing status.")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for processing"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            
        # Save the file
        file_path = os.path.join(UPLOADS_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the PDF
        collection_name = pdf_processor.process_pdf(file_path)
        
        return {
            "filename": file.filename,
            "status": "success",
            "message": "PDF processed successfully",
            "collection_name": collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/pdf",
    summary="List uploaded PDF files",
    description="Get a list of all PDF files that have been uploaded and processed.",
    response_description="Returns a list of PDF filenames.")
async def list_files():
    """List all uploaded PDF files"""
    try:
        files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf')]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/all",
    summary="Search across all PDFs",
    description="Search across all uploaded PDFs for an answer to a question.",
    response_description="Returns the answer with source attribution and confidence level.")
async def ask_all_pdfs(question: str = Query(...)):
    """Search across all PDFs for a question"""
    try:
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
            
        # Check if we have any PDFs loaded
        if not pdf_processor.knowledge_bases:
            return {
                "answer": "No PDFs have been uploaded yet. Please upload some PDFs first.",
                "source": "system",
                "confidence": "none",
                "details": "No documents available for search."
            }
            
        # Search across all PDFs
        try:
            result = pdf_processor.search_multiple_pdfs(question)
            return result
        except Exception as e:
            print(f"Error during PDF search: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error searching PDFs: {str(e)}"
            )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error in search endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.post("/voice/search/multiple",
    summary="Search across all PDFs using voice input",
    description="Search across all uploaded PDFs using voice input.",
    response_description="Returns the transcription and answer with source attribution.")
async def voice_search_multiple(audio: UploadFile = File(...)):
    """Search across all PDFs using voice input"""
    print("Received file:", audio.filename)
    print("Content type:", audio.content_type)

    raw = await audio.read()
    temp_audio_path = f"temp_audio_{uuid.uuid4().hex}"

    # Save with no extension first
    with open(temp_audio_path, "wb") as f:
        f.write(raw)

    # Try to decode based on MIME
    try:
        if "webm" in audio.content_type:
            temp_audio_path_wav = temp_audio_path + ".wav"
            audio_seg = AudioSegment.from_file(temp_audio_path, format="webm")
        elif "ogg" in audio.content_type:
            temp_audio_path_wav = temp_audio_path + ".wav"
            audio_seg = AudioSegment.from_file(temp_audio_path, format="ogg")
        elif "mp3" in audio.content_type:
            temp_audio_path_wav = temp_audio_path + ".wav"
            audio_seg = AudioSegment.from_file(temp_audio_path, format="mp3")
        elif "wav" in audio.content_type:
            temp_audio_path_wav = temp_audio_path + ".wav"
            audio_seg = AudioSegment.from_file(temp_audio_path, format="wav")
        else:
            raise HTTPException(status_code=400, detail="Unsupported audio format")

        # Normalize to PCM WAV
        audio_seg = audio_seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio_seg.export(temp_audio_path_wav, format="wav")

        question = audio_processor.transcribe_audio_file(temp_audio_path_wav)

        if not question:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        result = pdf_processor.search_multiple_pdfs(question)
        return {
            "transcription": question,
            **result
        }

    finally:
        safe_delete(temp_audio_path)
        if 'temp_audio_path_wav' in locals():
            safe_delete(temp_audio_path_wav)

@app.delete("/pdf/{filename}",
    summary="Delete a PDF file",
    description="Delete a specific PDF file and its associated collection from the knowledge base.",
    response_description="Returns the deletion status.")
async def delete_pdf(filename: str):
    """Delete a specific PDF file"""
    try:
        # Check if file exists
        file_path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        # Delete the file
        os.remove(file_path)
        
        # Delete the collection if it exists
        if filename in pdf_processor.knowledge_bases:
            collection_name = pdf_processor.knowledge_bases[filename]
            pdf_processor.chroma_client.delete_collection(collection_name)
            del pdf_processor.knowledge_bases[filename]
            
        return {
            "filename": filename,
            "status": "success",
            "message": "File and associated collection deleted successfully"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/policy",
    summary="Upload an insurance policy PDF",
    description="Upload an insurance policy PDF file for processing and due date tracking.",
    response_description="Returns the filename and processing status.")
async def upload_policy(file: UploadFile = File(...)):
    """Upload an insurance policy PDF file"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            
        # Save the file
        file_path = os.path.join(UPLOADS_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the PDF
        collection_name = pdf_processor.process_pdf(file_path)
        
        return {
            "filename": file.filename,
            "status": "success",
            "message": "Insurance policy processed successfully",
            "collection_name": collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies",
    summary="List insurance policies",
    description="Get a list of all insurance policy PDFs that have been uploaded.",
    response_description="Returns a list of policy information including due dates.")
async def list_policies():
    """List all uploaded insurance policy PDFs with due date information"""
    try:
        files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf')]
        policies = []
        
        for filename in files:
            # For now, we'll create mock due dates
            # In a real implementation, you'd extract due dates from the PDF content
            import random
            from datetime import datetime, timedelta
            
            # Generate a random due date within the next 30 days
            due_date = datetime.now() + timedelta(days=random.randint(1, 30))
            
            policies.append({
                "file_path": filename,
                "due_date": due_date.isoformat(),
                "status": "active"
            })
        
        return {"policies": policies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=9000, reload=True) 