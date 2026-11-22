import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("docnest.ollama")


class OllamaService:
    """
    Robust asynchronous connector for the local Ollama LLM runtime.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL
        self.timeout = float(settings.OLLAMA_TIMEOUT)

    @classmethod
    def ensure_ollama_daemon(cls) -> bool:
        """
        Verify if Ollama service is listening on configured host/port.
        If offline, attempt to spawn 'ollama serve' in background supervisor process.
        """
        import os
        import shutil
        import subprocess
        import socket
        import time
        from urllib.parse import urlparse

        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        host = "127.0.0.1"
        port = 11434
        try:
            parsed = urlparse(base_url)
            if parsed.hostname:
                host = parsed.hostname
            if parsed.port:
                port = parsed.port
        except Exception:
            pass

        # 1. Quick socket check
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.6)
        is_open = s.connect_ex((host, port)) == 0
        s.close()

        if is_open:
            logger.info(f"Ollama daemon is online at {base_url}.")
            return True

        # 2. Not open - attempt auto-start if on localhost
        if host in ("127.0.0.1", "localhost", "0.0.0.0"):
            possible_bins = [
                shutil.which("ollama"),
                os.path.expanduser("~/.local/bin/ollama"),
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
            ]
            bin_path = next((b for b in possible_bins if b and os.path.exists(b)), None)
            if not bin_path:
                logger.warning("Ollama binary not found on system PATH to auto-start.")
                return False

            logger.info(f"Auto-launching Ollama daemon via '{bin_path} serve'...")
            try:
                subprocess.Popen(
                    [bin_path, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
                # Wait up to 5 seconds for Ollama port to bind
                for _ in range(10):
                    time.sleep(0.5)
                    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s2.settimeout(0.5)
                    ready = s2.connect_ex((host, port)) == 0
                    s2.close()
                    if ready:
                        logger.info("Ollama daemon auto-started successfully and is now online.")
                        return True
            except Exception as e:
                logger.warning(f"Failed to auto-start Ollama daemon: {e}")

        return False

    async def check_health(self) -> Dict[str, Any]:
        """
        Verify connection to Ollama and determine available models.
        """
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    has_model = any(self.default_model in m for m in models)
                    return {
                        "connected": True,
                        "models": models,
                        "has_target_model": has_model,
                        "target_model": self.default_model,
                    }
        except Exception as exc:
            logger.warning(f"Ollama connection check failed: {exc}")
            return {
                "connected": False,
                "error": str(exc),
                "models": [],
                "has_target_model": False,
                "target_model": self.default_model,
            }
        return {"connected": False, "models": [], "has_target_model": False}

    async def get_active_model(self) -> str:
        """
        Determine the best active model to query, falling back to any available llama model.
        """
        health = await self.check_health()
        if not health.get("connected"):
            return self.default_model

        models: List[str] = health.get("models", [])
        # Prefer exact or close matches
        for m in models:
            if self.default_model in m:
                return m
        for m in models:
            if "llama" in m.lower():
                return m
        # Ignore embedding models
        for m in models:
            if "embed" not in m.lower():
                return m

        return models[0] if models else self.default_model

    async def rewrite_conversational_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> str:
        """
        Rewrite follow-up questions into standalone queries based on recent conversation turns.
        """
        if not chat_history or not query.strip():
            return query

        # Format recent history (up to last 4 turns)
        recent_history = chat_history[-4:]
        history_lines = []
        for msg in recent_history:
            sender = "User" if msg.get("role") in ["user", "human"] or msg.get("sender") == "user" else "Assistant"
            text = (msg.get("content") or msg.get("text") or "").strip()
            if text:
                history_lines.append(f"{sender}: {text[:200]}")

        if not history_lines:
            return query

        history_str = "\n".join(history_lines)
        prompt = f"""Given the following conversation history between a User and an Assistant, rewrite the User's latest question into a self-contained, standalone question suitable for document retrieval.
DO NOT answer the question. ONLY output the rewritten standalone question. If the question is already self-contained, output it unchanged.

Conversation History:
{history_str}

Latest User Question: {query}

Standalone Question:"""

        try:
            target_model = model or await self.get_active_model()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": target_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.0, "top_p": 0.8},
                    },
                )
                if resp.status_code == 200:
                    rewritten = resp.json().get("response", "").strip()
                    rewritten = rewritten.strip('"\'')
                    if rewritten and len(rewritten) > 3:
                        logger.info(f"Query rewritten: '{query}' -> '{rewritten}'")
                        return rewritten
        except Exception as e:
            logger.warning(f"Query rewriting failed ({e}), using raw query.")

        return query

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Generate completion using Ollama HTTP API with timeout protection and structured error handling.
        """
        target_model = model or await self.get_active_model()
        url = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            logger.info(f"Dispatching query to Ollama model '{target_model}'...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("response", "").strip()
                    return answer
                elif resp.status_code == 404:
                    return (
                        f"Ollama error: Model '{target_model}' not found. "
                        f"Run `ollama pull {target_model}` to download it."
                    )
                else:
                    return f"Ollama generation failed (HTTP {resp.status_code}): {resp.text}"

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}.")
            return (
                "Cannot connect to the local Ollama service. "
                "Please verify that Ollama is running (`ollama serve`)."
            )
        except httpx.TimeoutException:
            logger.error(f"Ollama generation timed out after {self.timeout}s.")
            return "Response generation timed out. Please try a simpler query or check system load."
        except Exception as exc:
            logger.error(f"Unexpected Ollama client error: {exc}", exc_info=True)
            return f"An error occurred while generating the answer: {str(exc)}"

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """
        Stream generated tokens from Ollama /api/generate via httpx streaming.
        """
        target_model = model or await self.get_active_model()
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature, "top_p": 0.9},
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except Exception:
                            continue
        except Exception as exc:
            logger.error(f"Error in Ollama token streaming: {exc}")
            yield f"\n[Stream interrupted: {exc}]"


# Global Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service

