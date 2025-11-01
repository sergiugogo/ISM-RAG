import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from ollama import Client
from typing import List, Dict, Any
import json

load_dotenv()

class RAGEngine:
    def __init__(self, persist_directory="../chroma_store"):
        """
        Initialize RAG engine with multilingual embeddings and persistent storage.
        
        Args:
            persist_directory: Path to ChromaDB persistent storage
        """
        # Initialize multilingual embeddings model (supports 50+ languages including Romanian and English)
        self.embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("documents")

        # Load LLM configuration from environment
        self.model_name = os.getenv("MODEL_NAME", "gpt-oss:120b")
        self.api_key = os.getenv("OLLAMA_API_KEY")

        # Initialize Ollama Cloud client
        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY not found in environment variables")
        
        self.llm_client = Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    def add_document(self, text: str, doc_id: str, metadata: Dict[str, Any] = None):
        """
        Add a single document chunk to the vector database.
        
        Args:
            text: The text content to index
            doc_id: Unique identifier for this chunk
            metadata: Dictionary with source information (filename, page_number, etc.)
        """
        if metadata is None:
            metadata = {}
            
        embeddings = self.embedder.encode([text])
        self.collection.add(
            documents=[text],
            embeddings=embeddings.tolist(),
            ids=[doc_id],
            metadatas=[metadata]
        )

    def add_documents_batch(self, documents: List[Dict[str, Any]]):
        """
        Add multiple documents in a batch for better performance.
        
        Args:
            documents: List of dicts with 'text', 'doc_id', and 'metadata' keys
        """
        if not documents:
            return
            
        texts = [doc['text'] for doc in documents]
        doc_ids = [doc['doc_id'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]
        
        embeddings = self.embedder.encode(texts)
        
        self.collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=doc_ids,
            metadatas=metadatas
        )

    def query(self, question: str, top_k=3) -> List[Dict[str, Any]]:
        """
        Caută documente relevante în baza vectorială și returnează cu metadata.
        
        Args:
            question: The query text
            top_k: Number of results to return
            
        Returns:
            List of dicts with 'text', 'metadata', and 'distance' keys
        """
        q_emb = self.embedder.encode([question])
        results = self.collection.query(
            query_embeddings=q_emb.tolist(), 
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results["documents"] or not results["documents"][0]:
            return []
        
        # Format results with metadata
        formatted_results = []
        for i, doc in enumerate(results["documents"][0]):
            result = {
                'text': doc,
                'metadata': results["metadatas"][0][i] if results["metadatas"] else {},
                'distance': results["distances"][0][i] if results["distances"] else None
            }
            formatted_results.append(result)
        
        return formatted_results

    def generate_answer(self, question: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generează răspunsul final cu referințe la surse.
        
        Args:
            question: The user's question
            context_docs: List of retrieved documents with metadata
            
        Returns:
            Dict with 'answer' and 'sources' keys
        """
        if not context_docs:
            return {
                "answer": "Nu am găsit nicio informație relevantă în documente pentru această întrebare.",
                "sources": []
            }

        # Build context from documents
        context = "\n\n".join([f"[Document {i+1}]: {doc['text']}" for i, doc in enumerate(context_docs)])
        
        prompt = f"""
        Context:
        {context}

        Întrebare: {question}

        Dacă răspunsul nu se găsește clar în context, răspunde cu:
        "Nu am găsit această informație în documente."
        
        Când răspunzi, menționează din ce document(e) provine informația (ex: "Conform Document 1...").
        Răspunde clar, concis și în limba română:
        """

        try:
            response = self.llm_client.chat(self.model_name, messages=[
                {"role": "user", "content": prompt}
            ])
            answer = response["message"]["content"]

            # Mini guardrail: dacă răspunsul e prea scurt/generic
            if len(answer.strip()) < 5:
                answer = "⚠️ Nu am găsit un răspuns clar în documente."

            # Extract and format sources - group by filename
            sources_by_file = {}
            for doc in context_docs:
                metadata = doc.get('metadata', {})
                filename = metadata.get('filename', 'Unknown')
                page_num = metadata.get('page_number')
                
                if filename not in sources_by_file:
                    sources_by_file[filename] = {
                        'filename': filename,
                        'pages': set(),
                        'chunks': [],
                        'min_distance': doc.get('distance', 1.0)
                    }
                
                if page_num:
                    sources_by_file[filename]['pages'].add(page_num)
                
                sources_by_file[filename]['chunks'].append({
                    'page': page_num,
                    'chunk_index': metadata.get('chunk_index'),
                    'distance': doc.get('distance')
                })
                
                # Track minimum distance (most relevant)
                if doc.get('distance') is not None:
                    sources_by_file[filename]['min_distance'] = min(
                        sources_by_file[filename]['min_distance'],
                        doc.get('distance')
                    )
            
            # Format sources list
            sources = []
            for idx, (filename, info) in enumerate(sources_by_file.items(), 1):
                pages_list = sorted(list(info['pages'])) if info['pages'] else []
                source_info = {
                    'document_index': idx,
                    'filename': filename,
                    'pages': pages_list,
                    'num_chunks': len(info['chunks']),
                    'relevance': 1 - info['min_distance'] if info['min_distance'] is not None else None
                }
                sources.append(source_info)

            return {
                "answer": answer,
                "sources": sources
            }

        except Exception as e:
            return {
                "answer": f"Eroare la generarea răspunsului: {e}",
                "sources": []
            }
