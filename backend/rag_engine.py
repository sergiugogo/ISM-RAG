import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from ollama import Client

load_dotenv()

class RAGEngine:
    def __init__(self, persist_directory="../chroma_store"):
        # Configurare embedder pentru text
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Configurare Chroma pentru stocarea vectorilor
        self.client = chromadb.Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection("documents")

        # Configurare LLM (Ollama Cloud)
        self.model_name = os.getenv("MODEL_NAME", "gpt-oss:120b")
        self.api_key = os.getenv("OLLAMA_API_KEY")

        # Inițializează clientul Ollama Cloud
        if not self.api_key:
            raise ValueError("⚠️  OLLAMA_API_KEY nu este setată în fișierul .env!")
        
        self.llm_client = Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    def add_document(self, text: str, doc_id: str):
        """Adaugă text în baza Chroma (cu embedding)"""
        embeddings = self.embedder.encode([text])
        self.collection.add(
            documents=[text],
            embeddings=embeddings.tolist(),
            ids=[doc_id]
        )

    def query(self, question: str, top_k=3):
        """Caută documente relevante în baza vectorială"""
        q_emb = self.embedder.encode([question])
        results = self.collection.query(query_embeddings=q_emb.tolist(), n_results=top_k)
        return results["documents"][0] if results["documents"] else []

    def generate_answer(self, question: str, context: str) -> str:
        """Generează răspunsul final, cu guardrails simple."""
        if not context.strip():
            return "Nu am găsit nicio informație relevantă în document pentru această întrebare."

        prompt = f"""
        Context:
        {context}

        Întrebare: {question}

        Dacă răspunsul nu se găsește clar în context, răspunde cu:
        "Nu am găsit această informație în document."
        Răspunde clar, concis și în limba română:
        """

        try:
            response = self.llm_client.chat(self.model_name, messages=[
                {"role": "user", "content": prompt}
            ])
            answer = response["message"]["content"]

            # Mini guardrail 2: dacă răspunsul e prea scurt/generic, model fallback
            if len(answer.strip()) < 5:
                return "⚠️ Nu am găsit un răspuns clar în document."

            # Mini guardrail 3: dacă răspunsul nu face referire la document
            if "nu am găsit" in answer.lower() or "nu se găsește" in answer.lower():
                return answer

            return answer

        except Exception as e:
            return f"Eroare la generarea răspunsului: {e}"
