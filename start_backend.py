#!/usr/bin/env python3
"""
Start script for the FastAPI backend server
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"Starting FastAPI server on {host}:{port}")
    print("Make sure you have set your OPENAI_API_KEY in the .env file")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        "app.api.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    ) 