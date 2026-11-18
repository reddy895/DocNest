import logging
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
from backend.app.core.config import settings
from backend.app.services.chunker import DocumentChunk

logger = logging.getLogger("docnest.bm25")


class BM25Service:
    """
    Persistent sparse keyword retriever implementing BM25Okapi scoring.
    Maintains synchronization with ChromaDB vector store and persists index to disk.
    """

    def __init__(self, index_dir: Optional[Path] = None):
        self.index_dir = index_dir or settings.BM25_DIR
        self.index_file = self.index_dir / "bm25_store.pkl"
        # In-memory corpus: chunk_id -> {text, doc_id, workspace_id, metadata}
        self.corpus: Dict[str, Dict[str, Any]] = {}
        self._bm25: Optional[BM25Okapi] = None
        self._doc_ids: List[str] = []  # parallel list to BM25 documents
        self.load()

    def _tokenize(self, text: str) -> List[str]:
        """Simple, fast tokenization for sparse keyword matching."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [t for t in tokens if len(t) > 1]

    def _rebuild_index(self) -> None:
        """Reconstruct BM25Okapi model from current in-memory corpus."""
        self._doc_ids = list(self.corpus.keys())
        tokenized_corpus = [
            self._tokenize(self.corpus[cid]["text"]) for cid in self._doc_ids
        ]
        if tokenized_corpus:
            self._bm25 = BM25Okapi(tokenized_corpus)
        else:
            self._bm25 = None

    def save(self) -> None:
        """Persist corpus to disk."""
        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            with open(self.index_file, "wb") as f:
                pickle.dump(self.corpus, f)
            logger.debug(f"BM25 index saved with {len(self.corpus)} chunks.")
        except Exception as e:
            logger.error(f"Failed to persist BM25 index: {e}")

    def load(self) -> None:
        """Load corpus from disk and build in-memory BM25Okapi model."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "rb") as f:
                    self.corpus = pickle.load(f)
                self._rebuild_index()
                logger.info(f"Loaded BM25 index with {len(self.corpus)} indexed chunks.")
            except Exception as e:
                logger.error(f"Failed to load BM25 index from {self.index_file}: {e}")
                self.corpus = {}
                self._bm25 = None
        else:
            self.corpus = {}
            self._bm25 = None

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add or update chunks in the BM25 index and save to disk."""
        if not chunks:
            return
        for chunk in chunks:
            self.corpus[chunk.chunk_id] = {
                "text": chunk.text,
                "doc_id": chunk.doc_id,
                "filename": chunk.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "workspace_id": getattr(chunk.metadata, "workspace_id", "Default Workspace"),
                "section_heading": getattr(chunk.metadata, "section_heading", None),
            }
        self._rebuild_index()
        self.save()

    def remove_document(self, doc_id: str) -> int:
        """Remove all chunks associated with a document ID."""
        to_delete = [cid for cid, item in self.corpus.items() if item["doc_id"] == doc_id]
        for cid in to_delete:
            del self.corpus[cid]
        if to_delete:
            self._rebuild_index()
            self.save()
        return len(to_delete)

    def search(
        self,
        query: str,
        top_k: int = 20,
        doc_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """
        Query BM25 index and return sorted list of (chunk_id, bm25_score).
        """
        if not self._bm25 or not self._doc_ids or not query.strip():
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)

        # Pair scores with chunk IDs and filter by doc_ids / workspace
        scored_candidates = []
        for cid, score in zip(self._doc_ids, scores):
            if score <= 0.0:
                continue
            item = self.corpus[cid]
            if doc_ids and item["doc_id"] not in doc_ids:
                continue
            if workspace_id and item.get("workspace_id") != workspace_id:
                continue
            scored_candidates.append((cid, float(score)))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]


# Module singleton
_bm25_instance: Optional[BM25Service] = None


def get_bm25_service() -> BM25Service:
    global _bm25_instance
    if _bm25_instance is None:
        _bm25_instance = BM25Service()
    return _bm25_instance
