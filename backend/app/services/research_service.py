import logging
import time
from typing import List, Dict, Any, Optional
from backend.app.services.chroma_service import get_chroma_service
from backend.app.services.bm25_service import get_bm25_service
from backend.app.services.ollama_service import get_ollama_service
from backend.app.core.database import get_db_connection

logger = logging.getLogger("docnest.research")


class ResearchService:
    """
    NotebookLM-style research intelligence engine providing:
    - Multi-mode grounded document summarization
    - Multi-document comparative analysis & contradiction detection
    - Probing questions, MCQs quiz generator, and flashcard creation
    """

    def __init__(self):
        self.chroma = get_chroma_service()
        self.bm25 = get_bm25_service()
        self.ollama = get_ollama_service()

    async def _gather_document_context(
        self, doc_ids: Optional[List[str]] = None, max_chars: int = 12000
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Retrieve representative text chunks from BM25 corpus and ChromaDB for specified doc_ids.
        """
        corpus = self.bm25.corpus or {}
        chunks_to_use = []

        if corpus:
            for cid, info in corpus.items():
                if not doc_ids or info.get("doc_id") in doc_ids:
                    chunks_to_use.append({
                        "chunk_id": cid,
                        "doc_id": info.get("doc_id", ""),
                        "filename": info.get("filename", "Document"),
                        "page_number": info.get("page_number", 1),
                        "chunk_index": info.get("chunk_index", 0),
                        "text": info.get("text", ""),
                        "section_heading": info.get("section_heading"),
                    })
        elif self.chroma._collection and self.chroma._collection.count() > 0:
            where_filter = None
            if doc_ids and len(doc_ids) == 1:
                where_filter = {"doc_id": doc_ids[0]}
            elif doc_ids and len(doc_ids) > 1:
                where_filter = {"doc_id": {"$in": doc_ids}}

            raw = self.chroma._collection.get(where=where_filter, limit=50)
            ids = raw.get("ids", [])
            docs = raw.get("documents", [])
            metas = raw.get("metadatas", [])
            for cid, doc, meta in zip(ids, docs, metas):
                chunks_to_use.append({
                    "chunk_id": cid,
                    "doc_id": meta.get("doc_id", "") if meta else "",
                    "filename": meta.get("filename", "Document") if meta else "Document",
                    "page_number": meta.get("page_number", 1) if meta else 1,
                    "chunk_index": meta.get("chunk_index", 0) if meta else 0,
                    "text": doc,
                    "section_heading": meta.get("section_heading") if meta else None,
                })

        context_blocks = []
        sources = []
        current_len = 0

        for c in chunks_to_use:
            heading_txt = f" - {c['section_heading']}" if c.get('section_heading') else ""
            block = f"[{c['filename']}, p.{c['page_number']}{heading_txt}]:\n{c['text']}\n"
            if current_len + len(block) > max_chars:
                break
            context_blocks.append(block)
            sources.append({
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "filename": c["filename"],
                "page_number": c["page_number"],
            })
            current_len += len(block)

        return "\n".join(context_blocks), sources

    async def summarize_documents(
        self,
        doc_ids: Optional[List[str]] = None,
        summary_type: str = "executive",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate grounded multi-mode document summary.
        Modes:
          - executive: High-level executive brief with core thesis
          - detailed: Structured section-by-section analytical breakdown
          - key_findings: Bulleted key takeaways, quantitative data, and insights
          - terms: Glossary of specialized domain terms and concepts
        """
        start_time = time.time()
        context_str, sources = await self._gather_document_context(doc_ids=doc_ids)

        if not context_str.strip():
            return {
                "summary_type": summary_type,
                "content": "No document content was found to summarize. Please ensure documents are uploaded and indexed.",
                "sources_used": 0,
                "processing_time_seconds": 0.0,
                "model_used": "none",
            }

        instructions_map = {
            "executive": (
                "Provide a high-level Executive Briefing summarizing the core objectives, major themes, "
                "and central conclusions of the documents. Include inline citations [Filename, p. X] for all factual points."
            ),
            "detailed": (
                "Provide an in-depth, structured Analytical Summary with clear headings, subheadings, and detailed explanations. "
                "Cover background, methodology, core findings, implications, and conclusions with inline citations [Filename, p. X]."
            ),
            "key_findings": (
                "Extract the top 5 to 10 Key Findings, critical statistics, quantitative metrics, and core takeaways. "
                "Format as crisp bullet points with inline citations [Filename, p. X]."
            ),
            "terms": (
                "Extract and define key technical terms, acronyms, methodologies, and specialized domain concepts introduced in the text. "
                "Format as a dictionary / glossary with definitions and page citations [Filename, p. X]."
            ),
        }

        instruction = instructions_map.get(summary_type, instructions_map["executive"])

        prompt = f"""DOCUMENT PASSAGES:
{context_str}

TASK:
{instruction}

STRICT GROUNDING RULES:
1. Base the summary strictly and exclusively on the passages provided above.
2. Cite all claims inline using [Filename, p. X].
3. Do not invent or assume outside information.

SUMMARY:"""

        active_model = model or await self.ollama.get_active_model()
        summary_text = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are DocNest Research Intelligence. Provide clear, highly structured, grounded document research summaries.",
            model=active_model,
            temperature=0.1,
        )

        elapsed = round(time.time() - start_time, 3)
        return {
            "summary_type": summary_type,
            "content": summary_text,
            "sources_used": len(sources),
            "processing_time_seconds": elapsed,
            "model_used": active_model,
        }


_research_service: Optional[ResearchService] = None


def get_research_service() -> ResearchService:
    global _research_service
    if _research_service is None:
        _research_service = ResearchService()
    return _research_service
