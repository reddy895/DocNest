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

    async def compare_documents(
        self,
        doc_ids: List[str],
        comparison_aspects: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct deep multi-document comparative analysis identifying:
        - Common core themes and agreements
        - Critical divergences and contradictions
        - Structured comparison matrix table
        """
        start_time = time.time()
        corpus = self.bm25.corpus or {}
        doc_groups: Dict[str, List[Dict[str, Any]]] = {}

        for cid, info in corpus.items():
            did = info.get("doc_id")
            if did in doc_ids:
                doc_groups.setdefault(did, []).append(info)

        # Fallback to Chroma if not populated
        if not doc_groups and self.chroma._collection:
            for did in doc_ids:
                raw = self.chroma._collection.get(where={"doc_id": did}, limit=25)
                for cid, doc, meta in zip(raw.get("ids", []), raw.get("documents", []), raw.get("metadatas", [])):
                    doc_groups.setdefault(did, []).append({
                        "filename": meta.get("filename", "Document"),
                        "page_number": meta.get("page_number", 1),
                        "text": doc,
                        "section_heading": meta.get("section_heading"),
                    })

        doc_blocks = []
        doc_names = []
        for did, items in doc_groups.items():
            fname = items[0].get("filename", did) if items else did
            doc_names.append(fname)
            sample_text = "\n".join([f"[{fname}, p.{it.get('page_number', 1)}]: {it.get('text', '')[:400]}" for it in items[:10]])
            doc_blocks.append(f"=== DOCUMENT: {fname} ===\n{sample_text}\n")

        full_doc_context = "\n".join(doc_blocks)
        aspects_str = ", ".join(comparison_aspects) if comparison_aspects else "methodology, key claims, metrics, scope, findings"

        prompt = f"""You are DocNest's Multi-Document Comparative Research Engine.
Perform a strict comparative analysis between the documents provided below.
Compare them on these aspects: {aspects_str}.

DOCUMENT DATA:
{full_doc_context}

OUTPUT IN EXACTLY THIS JSON FORMAT (valid raw JSON only, no markdown wrappers):
{{
  "overview": "Brief synthesis comparing scope and primary goals of the documents",
  "agreements": ["Shared finding or consensus point 1 [DocA, p. X; DocB, p. Y]", "Consensus point 2"],
  "contradictions": ["Divergence, discrepancy, or opposing claim 1 [DocA, p. X vs DocB, p. Y]", "Divergence point 2"],
  "matrix": "| Dimension | Document A | Document B |\\n| --- | --- | --- |\\n| Core Focus | ... | ... |\\n| Methodology | ... | ... |"
}}"""

        active_model = model or await self.ollama.get_active_model()
        raw_res = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are a senior document intelligence analyst. Compare documents strictly and output valid JSON.",
            model=active_model,
            temperature=0.1,
        )

        import json
        overview = "Comparative analysis of provided documents."
        agreements = []
        contradictions = []
        matrix = ""

        try:
            cleaned_json = raw_res.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()

            parsed = json.loads(cleaned_json)
            overview = parsed.get("overview", overview)
            agreements = parsed.get("agreements", [])
            contradictions = parsed.get("contradictions", [])
            matrix = parsed.get("matrix", "")
        except Exception as e:
            logger.warning(f"Could not parse LLM comparison JSON ({e}); using raw output as overview.")
            overview = raw_res

        elapsed = round(time.time() - start_time, 3)
        return {
            "documents_compared": doc_names or doc_ids,
            "overview": overview,
            "agreements": agreements,
            "contradictions": contradictions,
            "matrix": matrix,
            "processing_time_seconds": elapsed,
            "model_used": active_model,
        }

    async def generate_questions(
        self,
        doc_ids: Optional[List[str]] = None,
        count: int = 5,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate probing research questions grounded in documents."""
        start_time = time.time()
        context_str, _ = await self._gather_document_context(doc_ids=doc_ids, max_chars=8000)

        prompt = f"""DOCUMENT PASSAGES:
{context_str}

TASK:
Generate exactly {count} thought-provoking, high-level research questions that can be explored using the documents above.
Questions should test analytical understanding, methodologies, tradeoffs, and key findings.

OUTPUT FORMAT:
Return a valid raw JSON array of strings:
["Question 1?", "Question 2?", ...]"""

        active_model = model or await self.ollama.get_active_model()
        raw = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are an academic researcher formulating probing inquiry questions. Output valid JSON array only.",
            model=active_model,
            temperature=0.3,
        )

        import json
        questions = []
        try:
            cl = raw.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            elif "```" in cl:
                cl = cl.split("```")[1].split("```")[0].strip()
            parsed = json.loads(cl)
            if isinstance(parsed, list):
                questions = [str(q).strip() for q in parsed if q]
        except Exception:
            # Fallback line extraction
            questions = [line.lstrip("0123456789.-* ") for line in raw.splitlines() if "?" in line][:count]

        if not questions:
            questions = [
                "What are the primary methodologies and architectural choices described in the documents?",
                "What empirical results, benchmarks, or performance metrics are highlighted?",
                "What limitations, constraints, or security considerations are discussed?",
            ]

        return {
            "questions": questions[:count],
            "processing_time_seconds": round(time.time() - start_time, 3),
            "model_used": active_model,
        }

    async def generate_quiz(
        self,
        doc_ids: Optional[List[str]] = None,
        question_count: int = 5,
        difficulty: str = "medium",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate multiple choice questions with explanations and citations."""
        start_time = time.time()
        context_str, _ = await self._gather_document_context(doc_ids=doc_ids, max_chars=10000)

        prompt = f"""DOCUMENT PASSAGES:
{context_str}

TASK:
Create a {difficulty}-level multiple choice quiz with exactly {question_count} questions based strictly on the document context above.
For each question provide:
- question text
- 4 plausible options (A, B, C, D)
- exact correct_answer (must match one option verbatim)
- detailed explanation
- citation [Filename, p. X]

OUTPUT FORMAT (valid raw JSON only):
[
  {{
    "id": "q1",
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option B",
    "explanation": "...",
    "citation": "[Filename, p. X]"
  }}
]"""

        active_model = model or await self.ollama.get_active_model()
        raw = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are an educational assessment expert. Create grounded multiple-choice questions in strict JSON.",
            model=active_model,
            temperature=0.2,
        )

        import json
        import uuid
        quiz_items = []
        try:
            cl = raw.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            elif "```" in cl:
                cl = cl.split("```")[1].split("```")[0].strip()
            parsed = json.loads(cl)
            if isinstance(parsed, list):
                for item in parsed:
                    quiz_items.append({
                        "id": item.get("id") or f"q_{uuid.uuid4().hex[:6]}",
                        "question": item.get("question", ""),
                        "options": item.get("options", []),
                        "correct_answer": item.get("correct_answer", ""),
                        "explanation": item.get("explanation", ""),
                        "citation": item.get("citation"),
                    })
        except Exception as e:
            logger.warning(f"Failed to parse quiz JSON ({e}); creating fallback question.")

        if not quiz_items:
            quiz_items = [{
                "id": "q1",
                "question": "What is the primary topic addressed in the document context?",
                "options": ["Technical Architecture & Implementation", "Financial Audit", "Legal Discovery", "Marketing Strategy"],
                "correct_answer": "Technical Architecture & Implementation",
                "explanation": "Derived from the primary document sections and headings.",
                "citation": "Document, p. 1",
            }]

        return {
            "quiz": quiz_items[:question_count],
            "processing_time_seconds": round(time.time() - start_time, 3),
            "model_used": active_model,
        }

    async def generate_flashcards(
        self,
        doc_ids: Optional[List[str]] = None,
        card_count: int = 6,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate study flashcards for core definitions, concepts, and statistics."""
        start_time = time.time()
        context_str, _ = await self._gather_document_context(doc_ids=doc_ids, max_chars=10000)

        prompt = f"""DOCUMENT PASSAGES:
{context_str}

TASK:
Generate exactly {card_count} high-impact flashcards capturing critical concepts, formulas, findings, and terminology.
Each card must have:
- front: A concept, question, or term
- back: Concise, clear definition, explanation, or answer
- category: A category label (e.g. "Architecture", "Metric", "Security", "Terminology")
- citation: [Filename, p. X]

OUTPUT FORMAT (valid raw JSON array only):
[
  {{
    "id": "fc1",
    "front": "...",
    "back": "...",
    "category": "...",
    "citation": "[Filename, p. X]"
  }}
]"""

        active_model = model or await self.ollama.get_active_model()
        raw = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are a knowledge synthesis specialist. Generate clear, structured study flashcards in JSON format.",
            model=active_model,
            temperature=0.2,
        )

        import json
        import uuid
        cards = []
        try:
            cl = raw.strip()
            if "```json" in cl:
                cl = cl.split("```json")[1].split("```")[0].strip()
            elif "```" in cl:
                cl = cl.split("```")[1].split("```")[0].strip()
            parsed = json.loads(cl)
            if isinstance(parsed, list):
                for item in parsed:
                    cards.append({
                        "id": item.get("id") or f"fc_{uuid.uuid4().hex[:6]}",
                        "front": item.get("front", ""),
                        "back": item.get("back", ""),
                        "category": item.get("category", "Key Concept"),
                        "citation": item.get("citation"),
                    })
        except Exception as e:
            logger.warning(f"Failed to parse flashcards JSON ({e}); creating fallback cards.")

        if not cards:
            cards = [{
                "id": "fc1",
                "front": "Document Core Objective",
                "back": "Primary focus and technical/business goals described in the uploaded literature.",
                "category": "Overview",
                "citation": "Document, p. 1",
            }]

        return {
            "flashcards": cards[:card_count],
            "processing_time_seconds": round(time.time() - start_time, 3),
            "model_used": active_model,
        }


_research_service: Optional[ResearchService] = None


def get_research_service() -> ResearchService:
    global _research_service
    if _research_service is None:
        _research_service = ResearchService()
    return _research_service
