# Setup Instructions for PDF Q&A Assistant

## Prerequisites

1. **Python 3.8+** installed on your system
2. **OpenAI API Key** - Get one from [OpenAI Platform](https://platform.openai.com/api-keys)

## Step 1: Environment Setup

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Step 2: Configuration

1. **Create a `.env` file** in the root directory:
   ```bash
   # Copy the example file
   copy env_example.txt .env
   ```

2. **Edit the `.env` file** and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

## Step 3: Start the Application

### Option 1: Using the provided scripts (Recommended)

1. **Start the backend server** (in one terminal):
   ```bash
   python start_backend.py
   ```
   The backend will start on `http://localhost:8000`

2. **Start the frontend** (in another terminal):
   ```bash
   python start_frontend.py
   ```
   The frontend will open in your browser at `http://localhost:8501`

### Option 2: Manual startup

1. **Start the backend**:
   ```bash
   uvicorn app.api.main:app --host localhost --port 8000 --reload
   ```

2. **Start the frontend**:
   ```bash
   streamlit run app/app.py --server.port 8501
   ```

## Step 4: Using the Application

The application has three main tabs:

### 📚 PDF Upload & Search
- **Upload PDFs**: Upload one or multiple PDF files at once
- **Text Search**: Ask questions about your uploaded PDFs using text
- **Voice Search**: Ask questions using voice input
- All PDFs are automatically indexed and searchable together

### 🎤 Voice Search
- Quick voice search interface across all uploaded PDFs
- Shows current status of uploaded documents

### 📋 Insurance Policy Reminders
- Upload insurance policy PDFs
- Get due date reminders and policy management
- Track policy status and upcoming payments

**PDF Storage**: All PDFs are stored in: `C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\text_voice_chatbot\pdfs`

## Troubleshooting

### Connection Error (WinError 10061)
- **Cause**: Backend server is not running
- **Solution**: Make sure to start the backend first before the frontend

### OpenAI API Key Error
- **Cause**: Missing or invalid API key
- **Solution**: Check your `.env` file and ensure the API key is correct

### Missing Dependencies
- **Cause**: Not all packages installed
- **Solution**: Run `pip install -r requirements.txt` again

### Audio Recording Issues
- **Cause**: Missing audio dependencies
- **Solution**: Install additional audio packages:
  ```bash
   pip install pyaudio
   ```

### PDF Path Issues
- **Cause**: PDF directory doesn't exist
- **Solution**: The application will automatically create the PDF directory at:
  `C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\text_voice_chatbot\pdfs`

## API Endpoints

The backend provides these main endpoints:
- `POST /upload/pdf` - Upload a PDF file
- `POST /upload/policy` - Upload an insurance policy PDF
- `GET /files/pdf` - List uploaded PDFs
- `POST /ask/all` - Search across all PDFs
- `POST /voice/search/multiple` - Voice search across all PDFs
- `GET /policies` - List insurance policies with due dates
- `DELETE /pdf/{filename}` - Delete a PDF

## How It Works

1. **Upload**: Upload one or multiple PDFs through the interface
2. **Indexing**: PDFs are automatically processed and indexed into a vector database
3. **Search**: Ask questions in text or voice - the system searches across all uploaded PDFs
4. **Answers**: Get answers with source attribution and confidence levels

## File Structure

```
text_voice_chatbot/
├── app/
│   ├── api/
│   │   └── main.py          # FastAPI backend
│   ├── logic/
│   │   ├── pdf_processor.py # PDF processing logic
│   │   └── audio_processor.py # Audio processing logic
│   └── app.py               # Streamlit frontend
├── pdfs/                    # PDF storage directory (absolute path)
├── chroma_db/              # Vector database
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── start_backend.py        # Backend startup script
└── start_frontend.py       # Frontend startup script
```

## Support

If you encounter any issues:
1. Check that all dependencies are installed
2. Verify your OpenAI API key is correct
3. Ensure both backend and frontend are running
4. Check the console output for error messages
5. Verify the PDF directory exists and is writable 