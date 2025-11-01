"""
Script to reindex all documents with proper metadata.
Run this to update old documents that were indexed without metadata.
"""

import os
import json
from utils.pdf_loader import extract_text_by_pages, compute_file_hash
from utils.splitter import split_text_by_pages
from rag_engine import RAGEngine

def reindex_all_documents():
    """Reindex all documents in the uploads folder with proper metadata."""
    
    engine = RAGEngine()
    upload_dir = "uploads"
    processed_file_path = "processed_files.json"
    
    # Get all PDF files from upload directory
    pdf_files = [f for f in os.listdir(upload_dir) if f.endswith('.pdf')]
    
    print(f"\n{'='*60}")
    print(f"REINDEXING ALL DOCUMENTS")
    print(f"{'='*60}")
    print(f"Found {len(pdf_files)} PDF files\n")
    
    processed_registry = {}
    
    for i, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(upload_dir, filename)
        
        print(f"[{i}/{len(pdf_files)}] Processing: {filename}")
        
        try:
            # Compute file hash for change detection
            file_hash = compute_file_hash(file_path)
            
            # Extract text preserving page boundaries
            pages_text, page_count = extract_text_by_pages(file_path)
            
            # Split text into chunks with metadata
            base_metadata = {
                'filename': filename,
                'total_pages': page_count
            }
            chunks = split_text_by_pages(
                pages_text, 
                chunk_size=800, 
                overlap=100, 
                base_metadata=base_metadata
            )
            
            # Prepare documents for batch insertion
            documents_to_add = []
            for j, chunk_data in enumerate(chunks):
                doc_id = f"{filename}::{chunk_data['metadata'].get('page_number', 0)}::{j}"
                documents_to_add.append({
                    'text': chunk_data['text'],
                    'doc_id': doc_id,
                    'metadata': chunk_data['metadata']
                })
            
            # Batch insert into vector database
            engine.add_documents_batch(documents_to_add)
            
            # Update processing registry
            processed_registry[filename] = {
                'hash': file_hash,
                'chunk_count': len(chunks),
                'page_count': page_count
            }
            
            print(f"  [OK] Indexed {len(chunks)} chunks from {page_count} pages")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {filename}: {e}")
    
    # Save updated registry to disk
    with open(processed_file_path, 'w') as f:
        json.dump(processed_registry, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"REINDEXING COMPLETE")
    print(f"{'='*60}")
    print(f"Total documents processed: {len(processed_registry)}")
    print(f"Registry saved to: {processed_file_path}\n")


if __name__ == "__main__":
    reindex_all_documents()
