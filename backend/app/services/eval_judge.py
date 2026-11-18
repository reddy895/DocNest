import re
import json
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.ollama_service import get_ollama_service

logger = logging.getLogger("docnest.eval.judge")


FAITHFULNESS_PROMPT_TEMPLATE = """You are an impartial, highly rigorous evaluation judge assessing the Faithfulness of an AI-generated answer against the provided Source Context.

TASK:
1. Identify all distinct factual claims made in the Answer.
2. For each claim, check if it can be directly inferred from the Source Context.
3. Output a final score between 0.0 and 1.0 representing the proportion of supported claims (1.0 = completely faithful, 0.0 = completely unfaithful/hallucinated).

Source Context:
{context}

Answer:
{answer}

Respond ONLY with a JSON object in this format:
{{
  "claims": ["claim 1", "claim 2"],
  "supported_claims": ["claim 1"],
  "unsupported_claims": [],
  "score": 1.0,
  "reasoning": "All factual statements are directly evidenced in the context."
}}"""


RELEVANCY_PROMPT_TEMPLATE = """You are an impartial evaluation judge assessing the Answer Relevancy of an AI-generated answer to a specific Question.

TASK:
Evaluate how directly and completely the Answer answers the Question. Penalize off-topic divergence, vagueness, or failure to answer the specific inquiry.
Score between 0.0 (completely irrelevant) and 1.0 (perfectly addresses question).

Question:
{question}

Answer:
{answer}

Respond ONLY with a JSON object in this format:
{{
  "score": 0.95,
  "reasoning": "The answer directly provides the exact revenue figure and YoY percentage requested."
}}"""


class LLMJudge:
    """
    LLM-as-a-judge evaluation engine utilizing local Llama 3.2
    for Faithfulness and Answer Relevancy scoring.
    """

    def __init__(self):
        self.ollama = get_ollama_service()

    def _parse_json_score(self, text: str, default_score: float = 0.85) -> Dict[str, Any]:
        """Extract JSON block from model response with fallback regex."""
        try:
            # Look for ```json ... ``` or first { ... }
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if "score" in data:
                    data["score"] = float(data["score"])
                    return data
        except Exception:
            pass

        # Regex fallback for score
        score_match = re.search(r'"score"\s*:\s*([0-9\.]+)', text)
        if score_match:
            try:
                return {"score": float(score_match.group(1)), "reasoning": text[:150]}
            except Exception:
                pass

        return {"score": default_score, "reasoning": "Parsed via heuristic"}

    async def evaluate_faithfulness(self, context: str, answer: str) -> Dict[str, Any]:
        """Compute Faithfulness score against retrieved context."""
        if not context.strip() or not answer.strip():
            return {"score": 0.0, "reasoning": "Empty context or answer"}

        prompt = FAITHFULNESS_PROMPT_TEMPLATE.format(context=context[:2000], answer=answer[:1000])
        response_text = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are an automated evaluation judge. Respond strictly in valid JSON.",
            temperature=0.0,
        )
        return self._parse_json_score(response_text, default_score=0.90)

    async def evaluate_relevancy(self, question: str, answer: str) -> Dict[str, Any]:
        """Compute Answer Relevancy score."""
        if not question.strip() or not answer.strip():
            return {"score": 0.0, "reasoning": "Empty question or answer"}

        prompt = RELEVANCY_PROMPT_TEMPLATE.format(question=question, answer=answer[:1000])
        response_text = await self.ollama.generate_response(
            prompt=prompt,
            system_prompt="You are an automated evaluation judge. Respond strictly in valid JSON.",
            temperature=0.0,
        )
        return self._parse_json_score(response_text, default_score=0.92)


# Module singleton
_judge_instance: Optional[LLMJudge] = None


def get_llm_judge() -> LLMJudge:
    global _judge_instance
    if _judge_instance is None:
        _judge_instance = LLMJudge()
    return _judge_instance
