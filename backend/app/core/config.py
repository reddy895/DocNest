import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    DocNest Central Production Configuration Schema with environment variable override support.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DOCNEST_",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Settings
    ENV: str = "production"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    # JWT Authentication
    JWT_SECRET_KEY: str = "docnest_production_jwt_secret_key_change_in_env_2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DOCUMENTS_DIR: Path = Path("backend/documents")
    CHROMA_DIR: Path = Path("backend/chroma_db")
    BM25_DIR: Path = Path("backend/bm25_index")
    SAMPLES_DIR: Path = Path("backend/samples")
    DB_PATH: Path = Path("backend/docnest.db")
    COLLECTION_NAME: str = "docnest_collection"

    # RAG & Embedding Models (Quantized & Memory Efficient for 12GB RAM)
    EMBEDDING_MODEL: str = "nomic-embed-text"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    RETRIEVAL_TOP_K: int = 5
    MIN_RELEVANCE_SCORE: float = 0.30
    HYBRID_SEARCH_ENABLED: bool = True
    RERANKER_ENABLED: bool = True

    # Ollama LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 60

    # File Upload Security Constraints
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    def ensure_directories(self) -> None:
        """Create storage directories if they do not exist."""
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.BM25_DIR.mkdir(parents=True, exist_ok=True)
        self.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
