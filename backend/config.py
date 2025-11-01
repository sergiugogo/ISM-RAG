"""
Enterprise configuration for scalable RAG deployment.
Supports multiple vector databases and deployment strategies.
"""

import os
from typing import Literal, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import yaml

load_dotenv()


class VectorDBConfig(BaseModel):
    """Configuration for vector database."""
    
    provider: Literal["chromadb", "pinecone", "weaviate", "qdrant"] = Field(
        default="chromadb",
        description="Vector database provider"
    )
    
    # ChromaDB specific
    persist_directory: str = Field(
        default="../chroma_store",
        description="Directory for ChromaDB persistence"
    )
    
    # Cloud vector DB configs
    api_key: Optional[str] = Field(
        default=None,
        description="API key for cloud vector databases"
    )
    
    host: Optional[str] = Field(
        default=None,
        description="Host URL for cloud vector databases"
    )
    
    index_name: str = Field(
        default="documents",
        description="Name of the vector index/collection"
    )
    
    dimension: int = Field(
        default=384,
        description="Embedding dimension (384 for all-MiniLM-L6-v2)"
    )


class EmbeddingConfig(BaseModel):
    """Configuration for embedding models."""
    
    model_name: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )
    
    batch_size: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )
    
    device: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description="Device for embedding computation"
    )


class LLMConfig(BaseModel):
    """Configuration for LLM."""
    
    provider: Literal["ollama", "openai", "anthropic", "azure"] = Field(
        default="ollama",
        description="LLM provider"
    )
    
    model_name: str = Field(
        default="gpt-oss:120b",
        description="Model name/identifier"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="API key for LLM provider"
    )
    
    host: str = Field(
        default="https://ollama.com",
        description="API host URL"
    )
    
    temperature: float = Field(
        default=0.1,
        description="Temperature for response generation"
    )
    
    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens in response"
    )


class ProcessingConfig(BaseModel):
    """Configuration for document processing."""
    
    chunk_size: int = Field(
        default=800,
        description="Size of text chunks in characters"
    )
    
    chunk_overlap: int = Field(
        default=100,
        description="Overlap between chunks in characters"
    )
    
    max_workers: int = Field(
        default=4,
        description="Number of parallel workers for batch processing"
    )
    
    batch_insert_size: int = Field(
        default=100,
        description="Number of documents to insert per batch"
    )
    
    enable_ocr: bool = Field(
        default=True,
        description="Enable OCR for scanned documents"
    )


class RAGConfig(BaseModel):
    """Main RAG system configuration."""
    
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    
    top_k_results: int = Field(
        default=5,
        description="Number of documents to retrieve for context"
    )
    
    upload_directory: str = Field(
        default="uploads",
        description="Directory for uploaded files"
    )
    
    processed_files_path: str = Field(
        default="processed_files.json",
        description="Path to processed files registry"
    )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "RAGConfig":
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Load configuration from environment variables."""
        return cls(
            vector_db=VectorDBConfig(
                provider=os.getenv("VECTOR_DB_PROVIDER", "chromadb"),
                persist_directory=os.getenv("VECTOR_DB_PATH", "../chroma_store"),
                api_key=os.getenv("VECTOR_DB_API_KEY"),
                host=os.getenv("VECTOR_DB_HOST"),
                index_name=os.getenv("VECTOR_DB_INDEX", "documents"),
            ),
            embedding=EmbeddingConfig(
                model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
                device=os.getenv("EMBEDDING_DEVICE", "cpu"),
            ),
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "ollama"),
                model_name=os.getenv("MODEL_NAME", "gpt-oss:120b"),
                api_key=os.getenv("OLLAMA_API_KEY"),
                host=os.getenv("LLM_HOST", "https://ollama.com"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            ),
            processing=ProcessingConfig(
                chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
                chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
                max_workers=int(os.getenv("MAX_WORKERS", "4")),
                batch_insert_size=int(os.getenv("BATCH_INSERT_SIZE", "100")),
                enable_ocr=os.getenv("ENABLE_OCR", "true").lower() == "true",
            ),
            top_k_results=int(os.getenv("TOP_K_RESULTS", "5")),
            upload_directory=os.getenv("UPLOAD_DIR", "uploads"),
            processed_files_path=os.getenv("PROCESSED_FILES_PATH", "processed_files.json"),
        )
    
    def to_yaml(self, yaml_path: str):
        """Save configuration to YAML file."""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.dict(), f, default_flow_style=False)
    
    def get_vector_db_factory(self):
        """Get the appropriate vector database factory."""
        if self.vector_db.provider == "chromadb":
            return self._create_chromadb
        elif self.vector_db.provider == "pinecone":
            return self._create_pinecone
        elif self.vector_db.provider == "weaviate":
            return self._create_weaviate
        elif self.vector_db.provider == "qdrant":
            return self._create_qdrant
        else:
            raise ValueError(f"Unsupported vector DB: {self.vector_db.provider}")
    
    def _create_chromadb(self):
        """Create ChromaDB client."""
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.Client(
            Settings(persist_directory=self.vector_db.persist_directory)
        )
        return client.get_or_create_collection(self.vector_db.index_name)
    
    def _create_pinecone(self):
        """Create Pinecone client."""
        try:
            import pinecone
            
            pinecone.init(
                api_key=self.vector_db.api_key,
                environment=self.vector_db.host
            )
            
            # Create index if doesn't exist
            if self.vector_db.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    self.vector_db.index_name,
                    dimension=self.vector_db.dimension,
                    metric='cosine'
                )
            
            return pinecone.Index(self.vector_db.index_name)
        except ImportError:
            raise ImportError("Pinecone client not installed. Run: pip install pinecone-client")
    
    def _create_weaviate(self):
        """Create Weaviate client."""
        try:
            import weaviate
            
            client = weaviate.Client(
                url=self.vector_db.host,
                auth_client_secret=weaviate.AuthApiKey(api_key=self.vector_db.api_key)
            )
            
            return client
        except ImportError:
            raise ImportError("Weaviate client not installed. Run: pip install weaviate-client")
    
    def _create_qdrant(self):
        """Create Qdrant client."""
        try:
            from qdrant_client import QdrantClient
            
            if self.vector_db.host:
                client = QdrantClient(
                    url=self.vector_db.host,
                    api_key=self.vector_db.api_key
                )
            else:
                # Local mode
                client = QdrantClient(path=self.vector_db.persist_directory)
            
            return client
        except ImportError:
            raise ImportError("Qdrant client not installed. Run: pip install qdrant-client")


# Create default configuration
default_config = RAGConfig.from_env()
