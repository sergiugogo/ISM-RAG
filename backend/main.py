from fastapi import FastAPI, UploadFile, Form
from utils.pdf_loader import extract_text_from_pdf
from utils.splitter import split_text
from rag_engine import RAGEngine
import os
import json

app = FastAPI(title="ISM Portfolio")

engine = RAGEngine()

UPLOAD_DIR = "uploads"
PROCESSED_FILE_PATH = "processed_files.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Salvează fișierul
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Încarcă lista fișierelor deja procesate
    if os.path.exists(PROCESSED_FILE_PATH):
        with open(PROCESSED_FILE_PATH, "r") as f:
            processed = json.load(f)
    else:
        processed = {}

    # Verifică dacă fișierul a fost deja procesat
    if file.filename in processed:
        return {"message": f"📂 Fișierul '{file.filename}' a fost deja procesat anterior.", "chunks": 0}

    # Extrage textul (cu OCR doar la nevoie)
    text = extract_text_from_pdf(file_path)
    chunks = split_text(text)

    # Adaugă în Chroma
    for i, chunk in enumerate(chunks):
        engine.add_document(chunk, f"{file.filename}-{i}")

    # Salvează statusul fișierului procesat
    processed[file.filename] = True
    with open(PROCESSED_FILE_PATH, "w") as f:
        json.dump(processed, f, indent=2)

    print(f"✅ {file.filename} procesat — {len(chunks)} bucăți de text adăugate.")
    return {"message": "PDF procesat și adăugat în baza de date.", "chunks": len(chunks)}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    docs = engine.query(question)
    context = "\n\n".join(docs)
    answer = engine.generate_answer(question, context)
    return {"question": question, "answer": answer, "context": context}
