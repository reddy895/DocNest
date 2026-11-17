import logging
from typing import Optional, Dict, Any, List
import chromadb
from chromadb.api.models.Collection import Collection
from backend.app.core.config import settings
from backend.app.services.embedder import get_embedder

logger = logging.getLogger("docnest.chroma")


class ChromaService:
    """
    Manages the lifecycle, persistent storage, and querying of ChromaDB collections.
    """

    def __init__(self):
        self.persist_dir = str(settings.CHROMA_DIR)
        self.collection_name = settings.COLLECTION_NAME
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[Collection] = None
        self.initialize()

    def initialize(self) -> None:
        """Initialize Chroma PersistentClient and ensure target collection exists."""
        try:
            logger.info(f"Initializing ChromaDB PersistentClient at '{self.persist_dir}'...")
            settings.ensure_directories()
            self._client = chromadb.PersistentClient(path=self.persist_dir)

            embedder = get_embedder()

            # Initialize collection configured with cosine distance
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedder,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"ChromaDB collection '{self.collection_name}' ready. "
                f"Existing chunk count: {self._collection.count()}"
            )
        except Exception as exc:
            logger.error(f"Failed to initialize ChromaDB: {exc}", exc_info=True)
            raise RuntimeError(f"ChromaDB initialization failure: {exc}")

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self.initialize()
        return self._collection

    def count(self) -> int:
        """Return total indexed chunks in collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error reading collection count: {e}")
            return 0

    def reset_collection(self) -> None:
        """Reset and recreate the collection."""
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                pass
            self.initialize()


# Global Singleton instance
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
