import hashlib
import logging
import requests
from collections import OrderedDict
from typing import List, Optional, Any, Dict
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from backend.app.core.config import settings

logger = logging.getLogger("docnest.embedder")


class EmbeddingLRUCache:
    """Thread-safe LRU cache for computed embeddings to minimize inference load."""
    def __init__(self, maxsize: int = 2048):
        self.maxsize = maxsize
        self.cache: OrderedDict[str, List[float]] = OrderedDict()

    def _hash_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        k = self._hash_key(text)
        if k in self.cache:
            self.cache.move_to_end(k)
            return self.cache[k]
        return None

    def put(self, text: str, vector: List[float]) -> None:
        k = self._hash_key(text)
        if k in self.cache:
            self.cache.move_to_end(k)
        self.cache[k] = vector
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)


class OllamaNomicEmbedder(EmbeddingFunction[Documents]):
    """
    High-performance embedding function backed by Ollama's nomic-embed-text.
    Includes batching, automatic Ollama connection check, and transparent fallback
    to local SentenceTransformer (all-MiniLM-L6-v2) for maximum reliability on 12GB RAM systems.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        ollama_url: Optional[str] = None,
        batch_size: int = 32,
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.ollama_url = (ollama_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.batch_size = batch_size
        self._fallback_model: Optional[SentenceTransformer] = None
        self._use_ollama = True
        self._cache = EmbeddingLRUCache(maxsize=4096)
        self._check_ollama_availability()

    def _check_ollama_availability(self) -> None:
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                if any(self.model_name in m for m in models):
                    self._use_ollama = True
                    logger.info(f"Ollama nomic-embed-text verified online at {self.ollama_url}")
                    return
        except Exception as e:
            logger.warning(f"Ollama check failed: {e}. Falling back to SentenceTransformer.")
        self._use_ollama = False

    def _get_fallback_model(self) -> SentenceTransformer:
        if self._fallback_model is None:
            logger.info("Loading fallback SentenceTransformer model (all-MiniLM-L6-v2)...")
            self._fallback_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._fallback_model

    def _embed_via_ollama(self, texts: List[str]) -> List[List[float]]:
        # Call /api/embed (batch endpoint)
        url = f"{self.ollama_url}/api/embed"
        payload = {"model": self.model_name, "input": texts}
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings", [])
        if len(embeddings) != len(texts):
            raise ValueError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
        return embeddings

    def _embed_via_fallback(self, texts: List[str]) -> List[List[float]]:
        model = self._get_fallback_model()
        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vectors.tolist()

    def __call__(self, input: Documents) -> Embeddings:
        """Embed a list of text strings with LRU caching, batching, and fallback."""
        if not input:
            return []

        results: List[Optional[List[float]]] = [None] * len(input)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        # 1. Lookup in LRU cache
        for idx, text in enumerate(input):
            cached = self._cache.get(text)
            if cached is not None:
                results[idx] = cached
            else:
                missing_indices.append(idx)
                missing_texts.append(text)

        # 2. Batch compute missing embeddings
        if missing_texts:
            computed_embeddings: List[List[float]] = []
            for i in range(0, len(missing_texts), self.batch_size):
                batch = missing_texts[i : i + self.batch_size]
                if self._use_ollama:
                    try:
                        emb = self._embed_via_ollama(batch)
                        computed_embeddings.extend(emb)
                        continue
                    except Exception as exc:
                        logger.warning(f"Ollama embedding batch failed: {exc}. Using fallback.")
                        self._use_ollama = False

                fallback_emb = self._embed_via_fallback(batch)
                computed_embeddings.extend(fallback_emb)

            for original_idx, text, vector in zip(missing_indices, missing_texts, computed_embeddings):
                self._cache.put(text, vector)
                results[original_idx] = vector

        return results  # type: ignore

    def embed_query(self, input: Any = None, query: Any = None, *args, **kwargs) -> Any:
        """Chroma-compatible query embedding handler."""
        target = input if input is not None else query
        if target is None:
            return []
        if isinstance(target, str):
            target = [target]
        return self(target)


# Backward-compatible alias
LocalSentenceTransformerEmbedder = OllamaNomicEmbedder

# Module singleton
_embedder_instance: Optional[OllamaNomicEmbedder] = None


def get_embedder() -> OllamaNomicEmbedder:
    """Singleton getter for the primary embedding function."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = OllamaNomicEmbedder()
    return _embedder_instance
