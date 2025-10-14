Perfect 👏 — îți las mai jos un **README.md complet**, pregătit pentru GitHub și portofoliul ISM.
Totul e formatat frumos, cu emoji-uri, badge-uri și secțiuni clare.
Îl poți copia direct într-un fișier nou `README.md` din root-ul proiectului.

---

```markdown
# 📘 SmartDoc QA — AI Document Chat (RAG System)
> A project by **Innovative Software & Models SRL (ISM)**

[![Made with FastAPI](https://img.shields.io/badge/Made%20with-FastAPI-109989.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Made with Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg?style=flat-square&logo=streamlit)](https://streamlit.io/)
[![Vector DB](https://img.shields.io/badge/DB-ChromaDB-00C2CB.svg?style=flat-square&logo=database)](https://www.trychroma.com/)
[![AI Model](https://img.shields.io/badge/AI-Ollama%20Cloud-blue?logo=openai)](https://ollama.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🧠 Overview

**SmartDoc QA** is an AI-powered **Retrieval-Augmented Generation (RAG)** system  
that allows you to **upload any PDF document** and **ask natural-language questions** about its content.

It combines:
- 🔍 **ChromaDB** for vector-based semantic search  
- 🤖 **Ollama Cloud LLMs** (GPT-OSS, Mistral, etc.) for contextual answers  
- 🧾 **docTR OCR** for scanned documents (no need for Tesseract or Poppler)  
- ⚙️ **FastAPI + Streamlit** for a modern backend/frontend stack  

This project was built by **ISM (Innovative Software & Models SRL)** as a portfolio demo  
to showcase production-ready AI capabilities.

---

## ⚙️ Features

| Feature | Description |
|----------|-------------|
| 📄 **PDF Upload** | Upload any PDF — text-based or scanned |
| 🧠 **RAG Architecture** | Combines retrieval (ChromaDB) + generation (LLM) |
| 🧾 **OCR Integration** | Extracts text from images using docTR |
| ⚡ **One-Time Processing** | OCR & embeddings are generated once per file |
| 🧱 **Persistent Vector Store** | Uses ChromaDB with automatic on-disk persistence |
| 🚦 **Guardrails** | Detects missing context and prevents hallucinations |
| 💬 **Interactive UI** | Chat-style interface built with Streamlit |
| ☁️ **Cloud / Local LLMs** | Compatible with Ollama Cloud or local models |

---

## 🧩 Tech Stack

**Backend:**  
- FastAPI  
- ChromaDB  
- SentenceTransformers  
- docTR (OCR)  
- Ollama Cloud API  

**Frontend:**  
- Streamlit  
- Requests  
- Tailwind-style layout  

---

## 🗂️ Project Structure

```

RAG/
│
├── backend/
│   ├── main.py               # FastAPI routes (upload, ask)
│   ├── rag_engine.py         # Core RAG engine (search, generate)
│   ├── utils/
│   │   ├── pdf_loader.py     # Text extraction + OCR (docTR)
│   │   └── splitter.py       # Chunking logic
│   ├── uploads/              # Uploaded PDF files
│   ├── chroma_store/         # Persistent ChromaDB index
│   └── processed_files.json  # Cache of processed files
│
├── frontend/
│   ├── app.py                # Streamlit UI
│   └── requirements.txt
│
└── README.md                 # Project documentation

````

---

## 🚀 Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<sergiugogo>/ISM-RAG.git
cd ISM-RAG
````

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 4️⃣ Configure environment

Create a file `backend/.env`:

```bash
OLLAMA_API_KEY=your_ollama_api_key_here
MODEL_NAME=gpt-oss:20b
```

### 5️⃣ Run backend

```bash
cd backend
uvicorn main:app --reload
```

### 6️⃣ Run frontend

```bash
cd ../frontend
streamlit run app.py
```

Then open 👉 [http://localhost:8501](http://localhost:8501)

---

## 💬 Usage

1. Upload a PDF in the Streamlit interface.
2. The system will automatically:

   * extract text (OCR if needed)
   * create embeddings
   * store them in ChromaDB
3. Ask any question about the document:

   * “Care este numele persoanei din contract?”
   * “Ce spune articolul 3 despre durata contractului?”
4. Get an instant, AI-generated answer.

---

## 🧾 Example Output

**Upload response:**

```json
{
  "message": "PDF procesat și adăugat în baza de date.",
  "chunks": 12
}
```

**Ask response:**

```json
{
  "question": "Care este subsemnatul din această cerere?",
  "answer": "Subsemnatul din această cerere este Mozeș Ioan Andrei.",
  "context": "..."
}
```

---

## 🧱 Future Improvements

* [ ] Add multi-document RAG (cross-file context)
* [ ] Add conversation memory (chat history)
* [ ] Add streaming answers (real-time output)
* [ ] Add authentication for multiple users
* [ ] Deploy online via Render / Hugging Face Spaces

---

## 🏢 About ISM

> **Innovative Software & Models SRL (ISM)**
> Empowering businesses with intelligent automation and AI.

📍 Cluj-Napoca, România
🌐 Website: *coming soon*
📧 Contact: *[contact@ism-ai.ro](mailto:mogosansergiu39@gmail.com)*

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by Mogosan Sergiu-Ionut @ ISM**
*AI Developer & Founder – Innovative Software & Models SRL*

```