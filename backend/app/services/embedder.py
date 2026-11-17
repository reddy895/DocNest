import logging
from typing import List, Optional, Any
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from backend.app.core.config import settings

logger = logging.getLogger("docnest.embedder")


class LocalSentenceTransformerEmbedder(EmbeddingFunction[Documents]):
    """
    Robust embedding generator implementing ChromaDB's EmbeddingFunction interface
    backed by local SentenceTransformers (all-MiniLM-L6-v2).
    """

    def __init__(self, model_name: Optional[str] = None, batch_size: int = 32):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.batch_size = batch_size
        self._model: Optional[SentenceTransformer] = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model {self.model_name} loaded successfully.")
        except Exception as exc:
            logger.error(f"Failed to load embedding model '{self.model_name}': {exc}", exc_info=True)
            raise RuntimeError(f"Embedding initialization failed: {exc}")

    def __call__(self, input: Documents) -> Embeddings:
        """
        Embed a list of document strings with batching and error handling.
        """
        if not input:
            return []

        if self._model is None:
            self._load_model()

        try:
            # Generate normalized dense embeddings for cosine similarity
            vectors = self._model.encode(
                input,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return vectors.tolist()
        except Exception as exc:
            logger.error(f"Error generating embeddings for {len(input)} documents: {exc}")
            raise RuntimeError(f"Embedding generation failed: {exc}")

    def embed_query(self, input: Any = None, query: Any = None, *args, **kwargs) -> Any:
        """
        Embed queries for similarity search. Compatible with both ChromaDB
        embed_query(input=[...]) and custom embed_query(query='...').
        """
        target = input if input is not None else query
        if target is None:
            return []
        if isinstance(target, str):
            target = [target]
        return self(target)


# Module singleton
_embedder_instance: Optional[LocalSentenceTransformerEmbedder] = None


def get_embedder() -> LocalSentenceTransformerEmbedder:
    """Singleton getter for the embedding function."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = LocalSentenceTransformerEmbedder()
    return _embedder_instance
