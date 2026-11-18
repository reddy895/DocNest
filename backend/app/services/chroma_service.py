import logging
from typing import Optional, Dict, Any, List
import chromadb
from chromadb.api.models.Collection import Collection
import json
from pathlib import Path
from backend.app.core.config import settings
from backend.app.models.document import DocumentRecord, ChunkMetadata
from backend.app.models.schemas import Citation
from backend.app.services.chunker import DocumentChunk
from backend.app.services.embedder import get_embedder

logger = logging.getLogger("docnest.chroma")


class ChromaService:
    """
    Manages the lifecycle, persistent storage, and querying of ChromaDB collections.
    """

    def __init__(self):
        self.persist_dir = str(settings.CHROMA_DIR)
        self.collection_name = settings.COLLECTION_NAME
        self.registry_file = settings.DOCUMENTS_DIR / "registry.json"
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[Collection] = None
        self.initialize()

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load document metadata registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading document registry: {e}")
        return {}

    def _save_registry(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Save document metadata registry to disk."""
        try:
            settings.ensure_directories()
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving document registry: {e}")

    def save_document(
        self,
        doc_record: DocumentRecord,
        pdf_bytes: bytes,
        chunks: List[DocumentChunk],
    ) -> None:
        """
        Persist PDF bytes to disk, register document record,
        and batch upsert chunks into ChromaDB.
        """
        settings.ensure_directories()

        # 1. Save PDF file
        file_path = settings.DOCUMENTS_DIR / f"{doc_record.doc_id}.pdf"
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        doc_record.file_path = str(file_path)

        # 2. Upsert chunks into ChromaDB
        if chunks:
            ids = [c.chunk_id for c in chunks]
            documents = [c.text for c in chunks]
            metadatas = [c.metadata.to_chroma_metadata() for c in chunks]

            # Upsert in batches of 100 for stability
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                self.collection.upsert(
                    ids=ids[i : i + batch_size],
                    documents=documents[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                )

        # 3. Synchronize with BM25 sparse index
        try:
            from backend.app.services.bm25_service import get_bm25_service
            get_bm25_service().add_chunks(chunks)
        except Exception as bm_err:
            logger.warning(f"BM25 sync failed for doc {doc_record.doc_id}: {bm_err}")

        # 4. Update persistent registry
        registry = self._load_registry()
        registry[doc_record.doc_id] = doc_record.to_dict()
        self._save_registry(registry)
        logger.info(f"Document '{doc_record.filename}' ({doc_record.doc_id}) indexed successfully with {len(chunks)} chunks.")

    def find_document_by_hash(self, file_hash: str) -> Optional[DocumentRecord]:
        """
        Check if a document with identical SHA-256 hash has already been indexed.
        """
        registry = self._load_registry()
        for doc_data in registry.values():
            if doc_data.get("file_hash") == file_hash:
                return DocumentRecord(**doc_data)
        return None

    def find_document_by_id(self, doc_id: str) -> Optional[DocumentRecord]:
        """Retrieve document metadata by doc_id."""
        registry = self._load_registry()
        if doc_id in registry:
            return DocumentRecord(**registry[doc_id])
        return None

    def list_documents(self) -> List[DocumentRecord]:
        """Return all indexed documents sorted by upload date descending."""
        registry = self._load_registry()
        docs = [DocumentRecord(**d) for d in registry.values()]
        docs.sort(key=lambda d: d.upload_date, reverse=True)
        return docs

    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks for a document from ChromaDB, remove the PDF
        from disk, and purge its entry from the registry.
        Returns the number of deleted chunks.
        """
        registry = self._load_registry()
        if doc_id not in registry:
            return 0

        doc_data = registry[doc_id]
        filename = doc_data.get("filename", "")
        file_path_str = doc_data.get("file_path")

        chunks_deleted = 0
        # 1. Delete from ChromaDB using metadata filter
        try:
            # Query existing chunk count for this document
            existing = self.collection.get(where={"doc_id": doc_id})
            chunks_deleted = len(existing.get("ids", []))
            if chunks_deleted > 0:
                self.collection.delete(where={"doc_id": doc_id})
                logger.info(f"Deleted {chunks_deleted} chunks from ChromaDB for doc_id='{doc_id}'.")
        except Exception as e:
            logger.error(f"Error deleting chunks from ChromaDB for doc_id='{doc_id}': {e}")

        # 2. Synchronize removal in BM25 index
        try:
            from backend.app.services.bm25_service import get_bm25_service
            get_bm25_service().remove_document(doc_id)
        except Exception as bm_err:
            logger.warning(f"BM25 delete sync failed for doc {doc_id}: {bm_err}")

        # 3. Delete file from disk
        if file_path_str:
            p = Path(file_path_str)
            if p.exists():
                try:
                    p.unlink()
                    logger.info(f"Deleted physical document file: {p}")
                except Exception as e:
                    logger.warning(f"Could not remove document file {p}: {e}")

        # 3. Update registry
        del registry[doc_id]
        self._save_registry(registry)

        return chunks_deleted

    def query_documents(
        self,
        query_text: str,
        top_k: int = 4,
        doc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query vector collection for similar passages with optional document-level isolation.
        """
        total = self.count()
        if total == 0:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        # Build where clause if document isolation is requested
        where_filter: Optional[Dict[str, Any]] = None
        if doc_id:
            where_filter = {"doc_id": doc_id}
            # Verify document has chunks
            existing = self.collection.get(where=where_filter)
            doc_chunk_count = len(existing.get("ids", []))
            if doc_chunk_count == 0:
                return {
                    "ids": [[]],
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]],
                }
            effective_k = min(top_k, doc_chunk_count)
        else:
            effective_k = min(top_k, total)

        if effective_k <= 0:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        query_kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": effective_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)
        return results

    def query_collection(
        self,
        query_text: str,
        n_results: int = 20,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Query ChromaDB with custom where filter and return list of candidate items.
        """
        total = self.count()
        if total == 0:
            return []
        effective_k = min(n_results, total)
        if effective_k <= 0:
            return []

        kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": effective_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        try:
            res = self.collection.query(**kwargs)
        except Exception as e:
            logger.warning(f"Chroma query failed with filter {where_filter}: {e}")
            return []

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        ids = res.get("ids", [[]])[0]

        from types import SimpleNamespace
        candidates = []
        for i, text in enumerate(docs):
            dist = dists[i] if i < len(dists) else 1.0
            sim = max(0.0, min(1.0, 1.0 - dist))
            meta = metas[i] if i < len(metas) else {}
            cid = ids[i] if i < len(ids) else f"c_{i}"
            cand = SimpleNamespace(
                chunk_id=cid,
                doc_id=str(meta.get("doc_id", "")),
                filename=str(meta.get("filename", "")),
                page_number=int(meta.get("page_number", 1)),
                chunk_index=int(meta.get("chunk_index", i)),
                text=text,
                similarity_score=sim,
                metadata=SimpleNamespace(
                    section_heading=meta.get("section_heading"),
                    workspace_id=meta.get("workspace_id", "Default Workspace"),
                ),
            )
            candidates.append(cand)
        return candidates

    def get_relevant_chunks(
        self,
        query_text: str,
        top_k: int = 4,
        doc_id: Optional[str] = None,
        similarity_threshold: float = 0.25,
    ) -> List[Citation]:
        """
        Execute similarity search, convert distances to normalized relevance scores,
        filter against the similarity threshold, and return structured citations.
        """
        raw_results = self.query_documents(query_text=query_text, top_k=top_k, doc_id=doc_id)

        docs = raw_results.get("documents", [[]])[0]
        metas = raw_results.get("metadatas", [[]])[0]
        dists = raw_results.get("distances", [[]])[0]

        citations: List[Citation] = []

        for i, text in enumerate(docs):
            if not text or not text.strip():
                continue

            # Chroma cosine distance ranges from 0 (identical) to 2 (opposite)
            raw_distance = dists[i] if i < len(dists) else 1.0
            # Calculate similarity: 1.0 - distance
            similarity = max(0.0, min(1.0, 1.0 - raw_distance))

            meta = metas[i] if i < len(metas) else {}
            filename = str(meta.get("filename", "Document"))
            page_num = int(meta.get("page_number", 1))
            chunk_idx = int(meta.get("chunk_index", i))
            c_id = str(meta.get("chunk_id", f"c_{i}"))

            # Filter out chunks below relevance threshold
            if similarity < similarity_threshold:
                logger.debug(
                    f"Discarding chunk {c_id} with relevance {similarity:.3f} "
                    f"below threshold {similarity_threshold}"
                )
                continue

            citations.append(
                Citation(
                    source_id=c_id,
                    filename=filename,
                    page_number=page_num,
                    chunk_index=chunk_idx,
                    content=text.strip(),
                    relevance_score=round(similarity, 4),
                )
            )

        # Sort by relevance score descending
        citations.sort(key=lambda c: c.relevance_score, reverse=True)
        return citations

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
