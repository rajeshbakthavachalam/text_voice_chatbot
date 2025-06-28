# 📚 PDF Knowledge Base Q&A System

This is an improved version of the PDF Q&A system that uses a **persistent knowledge base** instead of re-uploading PDFs every time. The system automatically indexes PDFs from a designated directory and stores them in a vector database for fast and efficient searching.

## 🚀 Key Features

- **Persistent Knowledge Base**: PDFs are indexed once and stored permanently
- **Single PDF Search**: Ask questions about specific PDFs
- **Multi-PDF Search**: Search across all indexed PDFs simultaneously
- **Voice Search**: Ask questions using voice input (coming soon)
- **Easy Management**: Add/remove PDFs through the web interface
- **Fast Performance**: No need to re-upload or re-process PDFs

## 📁 Directory Structure

```
your_project/
├── C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\freelance\for_Rajesh\pdfs\  # PDF files location
│   ├── document1.pdf
│   ├── document2.pdf
│   └── document3.pdf
├── chroma_db/                     # Vector database storage (auto-created)
├── knowledge_base_manager.py      # Knowledge base management logic
├── knowledge_base_app.py          # Streamlit web application
├── initialize_knowledge_base.py   # Initialization script
└── requirements.txt
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Add Your PDFs

Place your PDF files in the PDFs directory:

```
C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\freelance\for_Rajesh\pdfs\
```

### 4. Initialize the Knowledge Base

Run the initialization script to index your PDFs:

```bash
python initialize_knowledge_base.py
```

This will:
- Check for PDFs in the PDFs directory
- Index all PDFs into the vector database
- Create a persistent knowledge base
- Show the status of the indexing process

### 5. Run the Web Application

```bash
streamlit run knowledge_base_app.py
```

## 🎯 How It Works

### 1. **PDF Indexing Process**
- PDFs are read and text is extracted
- Text is split into chunks (1000 characters with 200 character overlap)
- Chunks are converted to embeddings using HuggingFace embeddings
- Embeddings are stored in ChromaDB with metadata
- A knowledge base index is maintained for quick lookups

### 2. **Search Process**
- User asks a question (text or voice)
- Question is converted to embeddings
- Similar chunks are retrieved from the vector database
- LLM generates an answer based on retrieved context
- Answer is returned with source attribution

### 3. **Knowledge Base Management**
- **Add PDFs**: Place new PDFs in `pdfs/` directory and click "Index All PDFs"
- **Remove PDFs**: Use the remove button in the sidebar
- **Rebuild Index**: Use "Rebuild Index" to re-process all PDFs
- **Status Monitoring**: Check indexing status in the sidebar

## 🖥️ Using the Web Interface

### Sidebar Features
- **Status Metrics**: Shows total PDFs, indexed PDFs, and pending PDFs
- **Index Management**: Index all PDFs, rebuild index, remove individual PDFs
- **PDF List**: Shows all indexed PDFs with remove options

### Main Interface Tabs

#### 1. **Single PDF Search**
- Select a specific PDF from the dropdown
- Ask questions about that PDF only
- Get answers with source attribution

#### 2. **Multi-PDF Search**
- Ask questions that search across all indexed PDFs
- Get comprehensive answers from multiple sources
- See which PDFs were used as sources

#### 3. **Voice Search** (Coming Soon)
- Record voice questions
- Automatic transcription and search
- Support for both single and multi-PDF search

#### 4. **Knowledge Base Info**
- Detailed status information
- Technical details about the system
- Refresh status functionality

## 🔧 Advanced Usage

### Adding New PDFs

1. **Automatic Method**:
   - Place new PDFs in the PDFs directory: `C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\freelance\for_Rajesh\pdfs\`
   - Click "Index All PDFs" in the web interface
   - New PDFs will be automatically indexed

2. **Manual Method**:
   ```python
   from knowledge_base_manager import KnowledgeBaseManager
   
   kb = KnowledgeBaseManager()
   kb.index_pdf("new_document.pdf")
   ```

### Programmatic Access

```python
from knowledge_base_manager import KnowledgeBaseManager

# Initialize knowledge base
kb = KnowledgeBaseManager()

# Search in a specific PDF
result = kb.search_single_pdf("document.pdf", "What is the main topic?")

# Search across all PDFs
result = kb.search_all_pdfs("What are the key benefits?")

# Get knowledge base status
status = kb.get_knowledge_base_status()
```

### Customizing the System

#### Change PDF Directory
```python
kb = KnowledgeBaseManager(pdf_directory="my_pdfs", db_directory="my_db")
```

#### Modify Chunking Parameters
Edit `app/logic/pdf_processor.py`:
```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,      # Increase chunk size
    chunk_overlap=300,    # Increase overlap
    length_function=len
)
```

## 🚨 Troubleshooting

### Common Issues

1. **"No PDFs are indexed"**
   - Run `python initialize_knowledge_base.py`
   - Check that PDFs are in the PDFs directory: `C:\Users\rajes\OneDrive\Documents\Personal\practice_projects\freelance\for_Rajesh\pdfs\`

2. **"OpenAI API key not found"**
   - Set your OpenAI API key in the `.env` file
   - Restart the application

3. **"Error indexing PDF"**
   - Check PDF file is not corrupted
   - Ensure PDF contains extractable text
   - Check file permissions

4. **"ChromaDB connection error"**
   - Delete the `chroma_db/` directory
   - Re-run the initialization script

### Performance Tips

- **Large PDFs**: Consider splitting very large PDFs into smaller files
- **Memory Usage**: Monitor memory usage with many PDFs
- **Search Speed**: Results are cached for better performance

## 🔄 Migration from Old System

If you're migrating from the old upload-based system:

1. **Backup your data**: Copy any important PDFs from `uploads/` to `pdfs/`
2. **Run initialization**: `python initialize_knowledge_base.py`
3. **Test the new system**: `streamlit run knowledge_base_app.py`
4. **Remove old files**: Delete `uploads/` directory if no longer needed

## 📊 System Requirements

- **Python**: 3.8+
- **Memory**: 2GB+ RAM (more for large PDF collections)
- **Storage**: 1GB+ free space for vector database
- **Dependencies**: See `requirements.txt`

## 🤝 Contributing

Feel free to contribute improvements:
- Add new features
- Optimize performance
- Improve error handling
- Add more documentation

## 📝 License

This project is open source. Feel free to use and modify as needed. 