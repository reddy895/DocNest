from typing import List, Union, Dict, Any
from backend.app.services.chroma_service import get_chroma_service

_chroma = get_chroma_service()
collection = _chroma.collection


def add_document(doc_id: str, chunks: Union[List[str], str]) -> None:
    if isinstance(chunks, str):
        chunks = [chunks]
    valid_chunks = [c for c in chunks if c and c.strip()]
    if not valid_chunks:
        return
    ids = [f"{doc_id}_{i}" if len(valid_chunks) > 1 else doc_id for i in range(len(valid_chunks))]
    metadatas = [{"source": doc_id} for _ in valid_chunks]
    collection.upsert(ids=ids, documents=valid_chunks, metadatas=metadatas)


def search_documents(query: str, top_k: int = 4) -> Dict[str, Any]:
    total = collection.count()
    if total == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    n_results = min(top_k, total)
    return collection.query(query_texts=[query], n_results=n_results)
