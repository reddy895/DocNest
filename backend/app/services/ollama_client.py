import asyncio
import ollama
from typing import Optional
from backend.app.services.ollama_service import get_ollama_service


def generate_answer(prompt: str, model: Optional[str] = None) -> str:
    """
    Synchronous answer generator compatible with Streamlit.
    """
    ollama_srv = get_ollama_service()
    try:
        # Use asyncio run or direct ollama library
        target_model = model or "llama3.2"
        resp = ollama.generate(model=target_model, prompt=prompt)
        return resp.get("response", "")
    except Exception:
        try:
            return asyncio.run(ollama_srv.generate_response(prompt=prompt, model=model))
        except Exception as e:
            return f"Error connecting to Ollama: {e}"
