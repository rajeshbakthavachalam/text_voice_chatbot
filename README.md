# Text Voice Chatbot - Knowledge Base App

## Overview
This project is a Streamlit-based knowledge base and Q&A app that supports text and voice queries over a variety of document types (PDF, DOCX, CSV, TXT, RAR, ZIP, XLSX, JSON). It uses ChromaDB for vector storage and HuggingFace/SentenceTransformers for embeddings.

## Key Features
- Multi-format document ingestion and indexing
- FastAPI backend for API endpoints
- Streamlit frontend for interactive Q&A
- Voice and text search
- Hospital Bill Eligibility Check (with itemized bill analysis)
- Evaluation metrics and feedback logging

## Current Stable Checkpoint (June 28, 2025)
- **Meta tensor error is fixed**: The app sets `os.environ["CUDA_VISIBLE_DEVICES"] = ""` at the top of `app/logic/pdf_processor.py` and does not pass device kwargs to HuggingFaceEmbeddings. This avoids all meta/safe tensor errors without requiring package upgrades/downgrades.
- **Hospital Bill Eligibility Check tab**: The "Recheck Eligibility" and "Clear Results" buttons have been removed for a cleaner UI. All eligibility logic and results display remain intact.
- **All other functionalities are stable**: Document indexing, search, and feedback features are working as expected.
- **Safe for further UI changes and git commits**: This is a recommended checkpoint for version control.

## Setup Instructions
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional but recommended) Set up a Python virtual environment.
4. Place your documents in the `pdfs/` directory.
5. Run the backend:
   ```bash
   python start_backend.py
   ```
6. Run the frontend:
   ```bash
   streamlit run knowledge_base_app_tabs.py
   ```

## Troubleshooting
### Meta/Safe Tensor Error (PyTorch/SentenceTransformers)
If you see an error like:
```
NotImplementedError: Cannot copy out of meta tensor; no data! Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to() when moving module from meta to a different device.
```
- This is already fixed in this codebase. The fix is:
  - `os.environ["CUDA_VISIBLE_DEVICES"] = ""` is set at the very top of `app/logic/pdf_processor.py`.
  - HuggingFaceEmbeddings is initialized with only `model_name`, no device kwargs.
- **No further action is needed.**

## Customization & Further Development
- You can safely make further UI or backend changes from this checkpoint.
- For new features, create a new branch and commit your changes as needed.

## Contributing
Pull requests and issues are welcome!

## License
[MIT License](LICENSE)

# PDF Question Answering System

A powerful system for uploading, managing, and querying PDF documents using natural language. The system supports both text and voice-based queries across multiple PDFs.

## Features

- PDF upload and management
- Semantic search across multiple documents
- Question answering with source attribution
- Voice-based queries
- Document cleanup and maintenance

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Starting the API Server

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### PDF Management

1. Upload a single PDF:
```bash
POST /upload/pdf
Content-Type: multipart/form-data
file: <pdf_file>
```

2. Upload multiple PDFs:
```bash
POST /upload/multiple-pdfs
Content-Type: multipart/form-data
files: <pdf_files>
```

3. List uploaded PDFs:
```bash
GET /files/pdf
```

4. Delete a PDF:
```bash
DELETE /pdf/{filename}
```

#### Text Search

Search across all PDFs using text:
```bash
POST /search/multiple
Content-Type: application/json
{
    "question": "Your question here"
}
```

Response format:
```json
{
    "answer": "The answer to your question",
    "source": "multiple_documents",
    "confidence": 0.8,
    "details": {
        "sources": ["pdf1", "pdf2"],
        "total_sources_checked": 2
    }
}
```

#### Voice Search

Search across all PDFs using voice input:
```bash
POST /voice/search/multiple
Content-Type: audio/wav
<audio_data>
```

Response format:
```json
{
    "transcription": "Transcribed text from audio",
    "answer": "The answer to your question",
    "source": "multiple_documents",
    "confidence": 0.8,
    "details": {
        "sources": ["pdf1", "pdf2"],
        "total_sources_checked": 2
    }
}
```

### Testing the System

1. Test PDF Upload:
```bash
python test_api.py
```

2. Test Voice Search:
```bash
python test_voice_api.py
```

The voice search test will:
1. Check for available PDFs
2. Record your voice query
3. Send it to the API
4. Display the transcription and answer

### Using the Standalone Voice Search

For a more interactive experience, you can use the standalone voice search:
```bash
python voice_search.py
```

This provides a continuous conversation interface where you can:
- Ask questions using voice
- Get answers from all uploaded PDFs
- See which documents were used as sources
- Continue asking questions or exit with 'quit'

## Requirements

- Python 3.8+
- OpenAI API key
- PyAudio (for voice input)
- Other dependencies listed in requirements.txt

## Notes

- The system uses ChromaDB for vector storage
- PDFs are processed and stored in collections
- Voice input should be in WAV format (PCM encoding)
- The system supports searching across all uploaded PDFs simultaneously

## Error Handling

The system handles various error cases:
- Invalid PDF files
- Speech recognition failures
- API connection issues
- Missing PDFs
- Invalid audio format

## Contributing

Feel free to submit issues and enhancement requests!

# Insurance Policy Reminder API

This project provides an API to manage insurance policy reminders by extracting due dates from uploaded PDF files. It notifies users to pay their insurance premium before the due date.

## Features
- Upload insurance policy PDFs and extract due dates
- Store and list all uploaded policies
- Check for upcoming payment reminders (1 week before due date)
- Start/stop background monitoring for reminders
- Delete policies
- API endpoints for all operations
- Supports due dates in formats like `10/07/2025`, `10-07-2025`, and `July 10, 2025`

## Setup

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the API server**
   ```bash
   python app/api/insurance_api.py
   ```
   The server will start at `http://localhost:8000`

## API Endpoints

### 1. Upload Policy PDF
- **POST** `/upload/policy`
- **Body:** `form-data` with key `file` (type: File)
- **Response:**
  ```json
  {
    "message": "Policy uploaded and processed successfully",
    "file_path": "uploads/Policy_Reminder_1.pdf"
  }
  ```

### 2. List All Policies
- **GET** `/policies`
- **Response:**
  ```json
  [
    {
      "file_path": "uploads/Policy_Reminder_1.pdf",
      "due_date": "2025-07-10T00:00:00",
      "last_checked": "...",
      "notified": false
    }
  ]
  ```

### 3. Get a Specific Policy
- **GET** `/policy/{filename}`
- **Response:**
  ```json
  {
    "file_path": "uploads/Policy_Reminder_1.pdf",
    "due_date": "2025-07-10T00:00:00",
    "last_checked": "...",
    "notified": false
  }
  ```

### 4. Check Reminders
- **POST** `/check-reminders`
- **Response:**
  ```json
  [
    {
      "message": "Payment reminder",
      "policy_name": "Policy_Reminder_1.pdf",
      "due_date": "10/07/2025",
      "days_remaining": 3
    }
  ]
  ```
  *(Empty list if no reminders are due)*

### 5. Start Monitoring
- **POST** `/start-monitoring`
- **Response:**
  ```json
  { "message": "Monitoring service started" }
  ```

### 6. Stop Monitoring
- **POST** `/stop-monitoring`
- **Response:**
  ```json
  { "message": "Monitoring service stopped" }
  ```

### 7. Delete a Policy
- **DELETE** `/policy/{filename}`
- **Response:**
  ```json
  { "message": "Policy deleted successfully" }
  ```

## Supported Due Date Formats
- `Due Date: 10/07/2025`
- `Due Date: 10-07-2025`
- `Due Date: July 10, 2025`
- (Also works for `premium due`, `payment due`, `next payment`, `premium date`)

## Testing with Postman
1. **Upload a policy:**
   - POST `/upload/policy` with `form-data` key `file` (type: File)
2. **List all policies:**
   - GET `/policies`
3. **Get a specific policy:**
   - GET `/policy/{filename}`
4. **Check reminders:**
   - POST `/check-reminders`
5. **Start/Stop monitoring:**
   - POST `/start-monitoring` and `/stop-monitoring`
6. **Delete a policy:**
   - DELETE `/policy/{filename}`

## Notes
- The reminder system notifies you 1 week before the due date.
- If you want to see a reminder, upload a policy with a due date within the next 7 days.
- The monitoring service runs in the background and checks for reminders periodically.
- If you stop monitoring, it may take up to an hour to fully stop due to the current sleep interval.

## License
MIT