# DocNest Baseline Audit & Repository Assessment

**Audit Date:** November 2026  
**Repository:** `reddy895/DocNest`  
**Auditor:** Senior Full-Stack & RAG Architecture Team  

---

## 1. Executive Summary

DocNest is being transformed from an experimental monolithic Streamlit prototype into an enterprise-grade Document Intelligence and Retrieval-Augmented Generation (RAG) platform. This audit captures the baseline state of the repository, identifying architectural limitations, technical debt, and areas requiring remediation.

---

## 2. Inventory of Baseline Assets

| File / Directory | Baseline Purpose | Identified Weaknesses |
| :--- | :--- | :--- |
| `app.py` / `rag.py` | Monolithic Streamlit application UI | Tight coupling of UI, processing, and vector queries; lacks REST APIs; no authentication; synchronous blocking calls. |
| `document_processor.py` | Text extraction and character chunking | Basic `pypdf` extraction; lacks corrupt PDF handling, scanned page detection, and sentence-boundary preservation. |
| `vector_store.py` | ChromaDB collection wrapper | Direct collection calls; no document isolation filtering (`where={"doc_id": ...}`); lacks duplicate hash checks. |
| `ollama_client.py` | Ollama model invocation | Basic generate API; lacks streaming, timeout protection, and detailed prompt grounding templates. |
| `requirements.txt` | Python dependencies | Unpinned dependencies mixing frontend (Streamlit) and backend libraries. |
| `chroma_db/` | SQLite & HNSW vector store | Previously committed to Git; needs `.gitignore` exclusion and decoupled lifecycle management. |

---

## 3. Technology Baseline

- **Language:** Python 3.11 / 3.14
- **UI Framework:** Streamlit (Legacy monolith)
- **Vector Database:** ChromaDB (`PersistentClient`)
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
- **LLM Runtime:** Ollama (Local `llama3.2` 3B parameter model)
- **Document Ingestion:** PyPDF 7.0

---

## 4. Key Architectural Weaknesses Identified

1. **Tight Coupling:** The Streamlit script executes embeddings, file I/O, vector queries, and rendering in a single runtime loop.
2. **Missing Document Isolation:** Vector searches queried the entire collection without restricting search space to specific user-selected documents.
3. **No Duplicate Ingestion Detection:** Uploading the same PDF repeatedly resulted in redundant chunk embeddings.
4. **Weak Hallucination Controls:** Prompts lacked strict grounding directives, temperature constraints, and explicit unavailable-context phrasing.
5. **No Decoupled Frontend:** Incapable of serving headless web clients, mobile apps, or enterprise integrations via OpenAPI REST endpoints.

---

## 5. Transformation Roadmap

- **Backend:** FastAPI with modular routers (`/api/documents`, `/api/chat`, `/api/health`, `/api/settings`), Pydantic schemas, and robust background tasks.
- **Frontend:** React + Vite + Tailwind CSS styled with the mandatory **Forged Carbon (#202326)**, **Titanium Silver (#BFC3C7)**, and **Signal Yellow (#F4D21F)** design system (60:30:10 ratio).
- **RAG Engine:** Page-aware chunking, duplicate content hashing (SHA-256), metadata tagging, relevance score thresholds, and citation deep-linking.
- **Testing:** 100% automated pytest coverage for backend services and production Vite build validation for the frontend.
