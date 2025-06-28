from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.logic.insurance_reminder import InsuranceReminder
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Insurance Reminder API",
    description="API for managing insurance policy reminders",
    version="1.0.0"
)

# Initialize the insurance reminder system
reminder = InsuranceReminder()

# Pydantic models for request/response
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

# Notification callback function
def notification_callback(file_path: str, due_date: datetime, days_remaining: int):
    """Callback function for notifications"""
    policy_name = os.path.basename(file_path)
    logger.info(f"""
    ⚠️ INSURANCE PAYMENT REMINDER ⚠️
    ===============================
    Policy: {policy_name}
    Due Date: {due_date.strftime('%d/%m/%Y')}
    Days Remaining: {days_remaining}
    ===============================
    """)

# Set the notification callback
reminder.set_notification_callback(notification_callback)

@app.post("/upload/policy", response_model=Dict[str, str])
async def upload_policy(file: UploadFile = File(...)):
    """Upload an insurance policy PDF"""
    try:
        # Save the uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the policy
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
    """List all processed policies"""
    try:
        policies = reminder.get_all_policies()
        return policies
    except Exception as e:
        logger.error(f"Error listing policies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policy/{filename}", response_model=PolicyInfo)
async def get_policy(filename: str):
    """Get information about a specific policy"""
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
    """Delete a policy"""
    try:
        file_path = f"uploads/{filename}"
        if reminder.remove_policy(file_path):
            # Remove the actual file
            if os.path.exists(file_path):
                os.remove(file_path)
            return {"message": "Policy deleted successfully"}
        raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        logger.error(f"Error deleting policy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-reminders", response_model=List[ReminderResponse])
async def check_reminders(background_tasks: BackgroundTasks):
    """Check for upcoming payments and trigger notifications"""
    try:
        # Run the check in the background
        background_tasks.add_task(reminder.check_upcoming_payments)
        
        # Get all policies that need reminders
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
    """Start the monitoring service"""
    try:
        reminder.start_monitoring()
        return {"message": "Monitoring service started"}
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-monitoring")
async def stop_monitoring():
    """Stop the monitoring service"""
    try:
        reminder.stop_monitoring()
        return {"message": "Monitoring service stopped"}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 