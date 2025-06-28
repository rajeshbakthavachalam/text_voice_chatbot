import os
from app.logic.pdf_processor import PDFProcessor
from app.api.main import UPLOADS_DIR

def process_all_pdfs():
    """Process all PDFs in the uploads directory"""
    print("Initializing PDF processor...")
    pdf_processor = PDFProcessor()
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in uploads directory.")
        return
        
    print(f"\nFound {len(pdf_files)} PDF files to process:")
    for pdf_file in pdf_files:
        print(f"- {pdf_file}")
    
    print("\nProcessing PDFs...")
    for pdf_file in pdf_files:
        try:
            file_path = os.path.join(UPLOADS_DIR, pdf_file)
            print(f"\nProcessing {pdf_file}...")
            collection_name = pdf_processor.process_pdf(file_path)
            print(f"Successfully processed {pdf_file} into collection: {collection_name}")
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
    
    print("\nPDF processing complete!")
    print(f"Total collections created: {len(pdf_processor.knowledge_bases)}")

if __name__ == "__main__":
    process_all_pdfs() 