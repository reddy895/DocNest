import chromadb
from chromadb.utils import embedding_functions
from typing import List, Union, Dict, Any

# Persistent ChromaDB client so data is saved across app reruns
client = chromadb.PersistentClient(path="./chroma_db")

# Use SentenceTransformer embedding function (or default)
try:
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
except Exception:
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="college_rag_collection",
    embedding_function=embedding_fn
)


def add_document(doc_id: str, chunks: Union[List[str], str]) -> None:
    """
    Index document chunks into the Chroma collection.
    """
    if isinstance(chunks, str):
        chunks = [chunks]

    valid_chunks = [c for c in chunks if c and c.strip()]
    if not valid_chunks:
        return

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(valid_chunks):
        chunk_id = f"{doc_id}_{i}" if len(valid_chunks) > 1 else doc_id
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({"source": doc_id})

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )


def search_documents(query: str, top_k: int = 4) -> Dict[str, Any]:
    """
    Search the collection for similar documents given a query string.
    Returns ChromaDB query results dict.
    """
    total = collection.count()
    if total == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    n_results = min(top_k, total)
    return collection.query(
        query_texts=[query],
        n_results=n_results
    )

