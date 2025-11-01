from fastapi import FastAPI, UploadFile, Form
from utils.pdf_loader import extract_text_by_pages, compute_file_hash
from utils.splitter import split_text_by_pages
from rag_engine import RAGEngine
import os
import json

app = FastAPI(title="ISM Portfolio - Enterprise RAG")

engine = RAGEngine()

UPLOAD_DIR = "uploads"
PROCESSED_FILE_PATH = "processed_files.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_processed_files():
    """Load the registry of processed files with their hashes."""
    if os.path.exists(PROCESSED_FILE_PATH):
        with open(PROCESSED_FILE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_processed_files(processed):
    """Save the registry of processed files."""
    with open(PROCESSED_FILE_PATH, "w") as f:
        json.dump(processed, f, indent=2)

@app.post("/upload")
async def upload_file(file: UploadFile):
    """
    Upload and process a PDF file with incremental updates.
    Only reprocesses if the file content has changed.
    """
    # Save the file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Compute file hash for change detection
    file_hash = compute_file_hash(file_path)
    
    # Load processed files registry
    processed = load_processed_files()
    
    # Check if file was already processed with the same hash
    if file.filename in processed:
        stored_hash = processed[file.filename].get('hash')
        if stored_hash == file_hash:
            chunk_count = processed[file.filename].get('chunk_count', 0)
            return {
                "message": f"File '{file.filename}' already processed (unchanged)",
                "chunks": chunk_count,
                "status": "skipped"
            }
        else:
            print(f"[INFO] File '{file.filename}' modified. Reprocessing...")

    # Extract text by pages (preserves page numbers)
    pages_text, page_count = extract_text_by_pages(file_path)
    
    # Split text with metadata
    base_metadata = {
        'filename': file.filename,
        'total_pages': page_count
    }
    chunks = split_text_by_pages(pages_text, chunk_size=800, overlap=100, base_metadata=base_metadata)

    # Prepare documents for batch insertion
    documents_to_add = []
    for i, chunk_data in enumerate(chunks):
        doc_id = f"{file.filename}::{chunk_data['metadata'].get('page_number', 0)}::{i}"
        documents_to_add.append({
            'text': chunk_data['text'],
            'doc_id': doc_id,
            'metadata': chunk_data['metadata']
        })

    # Add to vector database in batch
    engine.add_documents_batch(documents_to_add)

    # Update processed files registry
    processed[file.filename] = {
        'hash': file_hash,
        'chunk_count': len(chunks),
        'page_count': page_count
    }
    save_processed_files(processed)

    print(f"[SUCCESS] {file.filename} processed - {len(chunks)} chunks indexed from {page_count} pages")
    return {
        "message": "PDF processed and indexed successfully",
        "chunks": len(chunks),
        "pages": page_count,
        "status": "processed"
    }

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    """
    Query the RAG system and get answers with source references.
    """
    # Query for relevant documents
    docs = engine.query(question, top_k=5)
    
    # Generate answer with sources
    result = engine.generate_answer(question, docs)
    
    return {
        "question": question,
        "answer": result['answer'],
        "sources": result['sources'],
        "num_sources": len(result['sources'])
    }
