# Merged FastAPI app: combines endpoints from main.py and insurance_api.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from typing import List, Optional, Dict
from urllib.parse import quote
from pydub import AudioSegment
import uuid
import time
from pydub.utils import mediainfo
from datetime import datetime, timedelta
from pathlib import Path
import sys
import logging
from pydantic import BaseModel

# --- PDF Q&A Imports ---
from ..logic.pdf_processor import PDFProcessor
from ..logic.audio_processor import AudioProcessor

# --- Insurance Reminder Imports ---
from ..logic.insurance_reminder import InsuranceReminder

# --- App Setup ---
app = FastAPI(
    title="Merged PDF Q&A and Insurance Reminder API",
    description="API for PDF Q&A and Insurance Policy Reminders",
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

# --- PDF Q&A Initialization ---
pdf_processor = PDFProcessor()
audio_processor = AudioProcessor()
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

def ensure_pcm_wav(input_path, output_path=None):
    if output_path is None:
        output_path = input_path
    try:
        print("Audio file info:", mediainfo(input_path))
        audio = AudioSegment.from_file(input_path, format="wav")
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(output_path, format="wav")
    except Exception as e:
        print(f"[Audio Error] Could not decode file: {e}")
        raise

def safe_delete(path, retries=20, delay=0.25):
    import time
    for _ in range(retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except Exception:
            time.sleep(delay)

# --- Insurance Reminder Initialization ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
reminder = InsuranceReminder()

# Pydantic models for insurance
class PolicyInfo(BaseModel):
    file_path: str
    due_date: datetime
    last_checked: datetime
    notified: bool

class ReminderResponse(BaseModel):
    message: str
    policy_name: str
    due_date: str
    days_remaining: int

def notification_callback(policy_name, due_date):
    logger.info(f"Reminder: Policy '{policy_name}' is due on {due_date}")

reminder.set_notification_callback(notification_callback)

# --- PDF Q&A Endpoints (from main.py) ---
@app.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        file_path = os.path.join(UPLOADS_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        collection_name = pdf_processor.process_pdf(file_path)
        return {
            "filename": file.filename,
            "status": "success",
            "message": "PDF processed successfully",
            "collection_name": collection_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/multiple-pdfs")
async def upload_multiple_pdfs(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        try:
            if not file.filename.endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "Only PDF files are allowed"
                })
                continue
            file_path = os.path.join(UPLOADS_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            collection_name = pdf_processor.process_pdf(file_path)
            results.append({
                "filename": file.filename,
                "status": "success",
                "message": "PDF processed successfully",
                "collection_name": collection_name
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    return {"results": results}

@app.get("/files/pdf")
async def list_files():
    try:
        files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf')]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/multiple")
async def search_multiple_pdfs(request: Request):
    try:
        data = await request.json()
        question = data.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        if not pdf_processor.knowledge_bases:
            return {
                "answer": "No PDFs have been uploaded yet. Please upload some PDFs first.",
                "source": "system",
                "confidence": "none",
                "details": "No documents available for search."
            }
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

@app.delete("/pdf/{filename}")
async def delete_pdf(filename: str):
    try:
        file_path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        os.remove(file_path)
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

@app.post("/cleanup")
async def cleanup_collections():
    try:
        pdf_files = set(f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf'))
        orphaned = []
        for filename, collection_name in pdf_processor.knowledge_bases.items():
            if filename not in pdf_files:
                try:
                    pdf_processor.chroma_client.delete_collection(collection_name)
                    orphaned.append(filename)
                except Exception as e:
                    print(f"Error deleting collection {collection_name}: {str(e)}")
        for filename in orphaned:
            del pdf_processor.knowledge_bases[filename]
        return {
            "status": "success",
            "message": f"Cleaned up {len(orphaned)} orphaned collections",
            "orphaned_collections": orphaned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/search/multiple")
async def voice_search_multiple(audio: UploadFile = File(...)):
    print("Received file:", audio.filename)
    print("Content type:", audio.content_type)
    raw = await audio.read()
    temp_audio_path = f"temp_audio_{uuid.uuid4().hex}"
    with open(temp_audio_path, "wb") as f:
        f.write(raw)
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

@app.post("/ask/pdf/{identifier}")
async def ask_pdf(identifier: str, question: str = Query(...)):
    try:
        result = pdf_processor.search_pdf(identifier, question)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/ask/all")
async def ask_all_pdfs(question: str = Query(...)):
    try:
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        if not pdf_processor.knowledge_bases:
            return {
                "answer": "No PDFs have been uploaded yet. Please upload some PDFs first.",
                "source": "system",
                "confidence": "none",
                "details": "No documents available for search."
            }
        result = pdf_processor.search_multiple_pdfs(question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/pdf/{identifier}/voice")
async def ask_pdf_voice(identifier: str, audio: UploadFile = File(...)):
    try:
        temp_audio_path = f"temp_{identifier}_{uuid.uuid4().hex}.wav"
        try:
            with open(temp_audio_path, "wb") as f:
                f.write(await audio.read())
            ensure_pcm_wav(temp_audio_path)
            question = audio_processor.transcribe_audio_file(temp_audio_path)
            if not question:
                raise HTTPException(status_code=400, detail="Could not transcribe audio")
            result = pdf_processor.search_pdf(identifier, question)
            return {
                "transcription": question,
                **result
            }
        finally:
            safe_delete(temp_audio_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Insurance Reminder Endpoints (from insurance_api.py) ---
@app.post("/upload/policy", response_model=Dict[str, str])
async def upload_policy(file: UploadFile = File(...)):
    try:
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        if reminder.process_policy_pdf(file_path):
            return {
                "message": "Policy uploaded and processed successfully",
                "file_path": file_path
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to process policy PDF")
    except Exception as e:
        logger.error(f"Error uploading policy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies", response_model=List[PolicyInfo])
async def list_policies():
    try:
        policies = reminder.get_all_policies()
        return policies
    except Exception as e:
        logger.error(f"Error listing policies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policy/{filename}", response_model=PolicyInfo)
async def get_policy(filename: str):
    try:
        file_path = f"uploads/{filename}"
        policy = reminder.get_policy_info(file_path)
        if policy:
            return policy
        raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        logger.error(f"Error getting policy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/policy/{filename}")
async def delete_policy(filename: str):
    try:
        file_path = f"uploads/{filename}"
        if reminder.remove_policy(file_path):
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"message": "Policy deleted successfully"}
        raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        logger.error(f"Error deleting policy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-reminders", response_model=List[ReminderResponse])
async def check_reminders(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(reminder.check_upcoming_payments)
        current_date = datetime.now()
        one_week_from_now = current_date + timedelta(days=7)
        reminders = []
        for policy in reminder.get_all_policies():
            if not policy['notified'] and current_date <= policy['due_date'] <= one_week_from_now:
                days_remaining = (policy['due_date'] - current_date).days
                reminders.append(ReminderResponse(
                    message="Payment reminder",
                    policy_name=os.path.basename(policy['file_path']),
                    due_date=policy['due_date'].strftime('%d/%m/%Y'),
                    days_remaining=days_remaining
                ))
        return reminders
    except Exception as e:
        logger.error(f"Error checking reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-monitoring")
async def start_monitoring():
    try:
        reminder.start_monitoring()
        return {"message": "Monitoring service started"}
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-monitoring")
async def stop_monitoring():
    try:
        reminder.stop_monitoring()
        return {"message": "Monitoring service stopped"}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 