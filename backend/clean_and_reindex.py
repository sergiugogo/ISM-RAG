"""
Clean ChromaDB and reindex all documents.
This will delete the old database and create a fresh one with proper metadata.
"""

import os
import shutil
from reindex_all import reindex_all_documents

def clean_and_reindex():
    """Delete existing ChromaDB and reindex all documents with fresh metadata."""
    
    chroma_dir = "../chroma_store"
    
    print("\n" + "="*60)
    print("CLEANING AND REINDEXING")
    print("="*60 + "\n")
    
    # Remove old vector database
    if os.path.exists(chroma_dir):
        print(f"[INFO] Deleting old ChromaDB at {chroma_dir}...")
        shutil.rmtree(chroma_dir)
        print("[OK] Old database deleted\n")
    else:
        print("[INFO] No existing database found\n")
    
    # Reindex all documents with proper metadata
    print("[INFO] Starting reindexing process...\n")
    reindex_all_documents()
    
    print("\n[SUCCESS] All documents have been properly indexed with metadata")


if __name__ == "__main__":
    clean_and_reindex()
