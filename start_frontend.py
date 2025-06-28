#!/usr/bin/env python3
"""
Start script for the Streamlit frontend
"""
import subprocess
import sys
import os

def start_streamlit():
    """Start the Streamlit frontend application"""
    try:
        # Check if streamlit is installed
        import streamlit
        print("Starting Streamlit frontend...")
        print("The app will open in your browser at http://localhost:8501")
        print("Make sure the backend is running on http://localhost:8000")
        print("Press Ctrl+C to stop the frontend")
        
        # Start streamlit with the app.py file
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except ImportError:
        print("Error: Streamlit is not installed.")
        print("Please install it with: pip install streamlit")
    except KeyboardInterrupt:
        print("\nFrontend stopped by user")
    except Exception as e:
        print(f"Error starting frontend: {e}")

if __name__ == "__main__":
    start_streamlit() 