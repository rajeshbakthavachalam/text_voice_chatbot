#!/usr/bin/env python3
"""
Initialize Knowledge Base Script

This script will:
1. Check for PDFs in the 'pdfs' directory
2. Index all PDFs into the knowledge base
3. Create a persistent vector database
4. Show the status of the knowledge base

Usage:
    python initialize_knowledge_base.py
"""

import os
import sys
from pathlib import Path
from knowledge_base_manager import KnowledgeBaseManager

def main():
    print("🚀 Initializing PDF Knowledge Base...")
    print("=" * 50)
    
    # Check if pdfs directory exists
    documents_dir = Path("pdfs")  # Use relative path to current project's pdfs directory
    if not documents_dir.exists():
        print("❌ Error: Documents directory not found!")
        print(f"💡 Expected location: {documents_dir}")
        print("💡 Please ensure the directory exists and contains document files.")
        return False
    
    # Get all supported document files (not just PDFs)
    supported_extensions = {'.pdf', '.docx', '.csv', '.txt', '.rar', '.zip', '.xlsx', '.json'}
    document_files = []
    for ext in supported_extensions:
        document_files.extend(list(documents_dir.glob(f"*{ext}")))
    
    if not document_files:
        print("❌ No supported document files found in documents directory!")
        print(f"💡 Please add some document files to: {documents_dir}")
        print(f"💡 Supported formats: {', '.join(supported_extensions)}")
        return False
    
    print(f"📁 Found {len(document_files)} document files:")
    for doc_file in document_files:
        print(f"   📄 {doc_file.name}")
    
    print("\n🔧 Initializing Knowledge Base Manager...")
    
    try:
        # Initialize knowledge base manager
        kb_manager = KnowledgeBaseManager()
        
        # Check current status
        status = kb_manager.get_knowledge_base_status()
        print(f"\n📊 Current Status:")
        print(f"   Total Documents: {status['total_documents']}")
        print(f"   Indexed Documents: {status['indexed_documents']}")
        print(f"   Pending Documents: {len(status['pending_documents'])}")
        
        if status['pending_documents']:
            print(f"\n⏳ Indexing {len(status['pending_documents'])} pending documents...")
            
            # Index all documents
            results = kb_manager.index_all_documents()
            
            # Show results
            print("\n📋 Indexing Results:")
            success_count = 0
            for doc_name, success in results.items():
                if success:
                    print(f"   ✅ {doc_name}")
                    success_count += 1
                else:
                    print(f"   ❌ {doc_name}")
            
            print(f"\n🎉 Successfully indexed {success_count}/{len(results)} documents!")
            
        else:
            print("\n✅ All documents are already indexed!")
        
        # Show final status
        final_status = kb_manager.get_knowledge_base_status()
        print(f"\n📊 Final Status:")
        print(f"   Total Documents: {final_status['total_documents']}")
        print(f"   Indexed Documents: {final_status['indexed_documents']}")
        print(f"   Pending Documents: {len(final_status['pending_documents'])}")
        
        if final_status['indexed_documents_list']:
            print(f"\n📖 Indexed Documents:")
            for doc_name in final_status['indexed_documents_list']:
                print(f"   📄 {doc_name}")
        
        print("\n🎯 Knowledge Base is ready!")
        print("💡 You can now run the Streamlit app:")
        print("   streamlit run knowledge_base_app.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing knowledge base: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure you have all required dependencies installed")
        print("   2. Check that your OpenAI API key is set in environment variables")
        print("   3. Ensure you have write permissions in the current directory")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 