import os
from dotenv import load_dotenv
import uvicorn

def check_environment():
    """Check if required environment variables are set"""
    load_dotenv()
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    return True

if __name__ == "__main__":
    if check_environment():
        print("Starting PDF Question Answering API server...")
        print("API documentation will be available at http://localhost:8000/docs")
        uvicorn.run(
            "app.api.merged_app:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        ) 