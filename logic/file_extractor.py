import os
import pdfplumber
import docx
import openpyxl
import zipfile
import rarfile
import json
import csv
import tempfile
import shutil

# Utility function to extract text from various file types

def extract_text_from_file(filepath):
    """
    Extract text from a file of various supported types.
    Supported: .pdf, .docx, .xlsx, .csv, .txt, .json, .zip, .rar
    Returns extracted text as a string.
    """
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".pdf":
            with pdfplumber.open(filepath) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        
        elif ext == ".docx":
            doc = docx.Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif ext == ".xlsx":
            wb = openpyxl.load_workbook(filepath, data_only=True)
            text = []
            for sheet in wb.worksheets:
                text.append(f"Sheet: {sheet.title}")
                for row in sheet.iter_rows(values_only=True):
                    row_text = " ".join([str(cell) if cell is not None else "" for cell in row])
                    if row_text.strip():
                        text.append(row_text)
            return "\n".join(text)
        
        elif ext == ".csv":
            text = []
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        if i == 0:  # Header row
                            text.append(f"Headers: {', '.join(str(cell) for cell in row)}")
                        else:
                            row_text = " | ".join(str(cell) for cell in row)
                            if row_text.strip():
                                text.append(f"Row {i}: {row_text}")
            except UnicodeDecodeError:
                # Try with different encoding
                with open(filepath, 'r', encoding='latin-1', errors='ignore') as f:
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        if i == 0:  # Header row
                            text.append(f"Headers: {', '.join(str(cell) for cell in row)}")
                        else:
                            row_text = " | ".join(str(cell) for cell in row)
                            if row_text.strip():
                                text.append(f"Row {i}: {row_text}")
            return "\n".join(text)
        
        elif ext == ".txt":
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(filepath, "r", encoding=encoding, errors="ignore") as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            # If all encodings fail, use binary mode
            with open(filepath, "rb") as f:
                return f.read().decode('utf-8', errors='ignore')
        
        elif ext == ".json":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        
        elif ext == ".zip":
            text = []
            with zipfile.ZipFile(filepath, "r") as z:
                for name in z.namelist():
                    if name.endswith("/"):  # skip directories
                        continue
                    try:
                        with z.open(name) as f:
                            # Create a temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(name)[1]) as tmp:
                                tmp.write(f.read())
                                tmp_path = tmp.name
                            
                            # Extract text from the temporary file
                            try:
                                extracted = extract_text_from_file(tmp_path)
                                if extracted.strip():
                                    text.append(f"File: {name}\n{extracted}")
                            except Exception as e:
                                text.append(f"File: {name} - Error: {str(e)}")
                            finally:
                                # Clean up temporary file
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                    except Exception as e:
                        text.append(f"Error processing {name}: {str(e)}")
            return "\n".join(text)
        
        elif ext == ".rar":
            text = []
            with rarfile.RarFile(filepath) as r:
                for name in r.namelist():
                    if name.endswith("/"):  # skip directories
                        continue
                    try:
                        with r.open(name) as f:
                            # Create a temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(name)[1]) as tmp:
                                tmp.write(f.read())
                                tmp_path = tmp.name
                            
                            # Extract text from the temporary file
                            try:
                                extracted = extract_text_from_file(tmp_path)
                                if extracted.strip():
                                    text.append(f"File: {name}\n{extracted}")
                            except Exception as e:
                                text.append(f"File: {name} - Error: {str(e)}")
                            finally:
                                # Clean up temporary file
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                    except Exception as e:
                        text.append(f"Error processing {name}: {str(e)}")
            return "\n".join(text)
        
        else:
            return f"[Unsupported file type: {ext}]"
            
    except Exception as e:
        return f"[Error extracting {filepath}: {e}]" 