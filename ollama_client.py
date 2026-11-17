import ollama
from typing import Optional


def get_preferred_model() -> str:
    default_model = "llama3.2"
    try:
        models_info = ollama.list()
        models = []
        if isinstance(models_info, dict) and "models" in models_info:
            models = [m.get("model") or m.get("name") or "" for m in models_info["models"]]
        elif hasattr(models_info, "models"):
            for m in models_info.models:
                name = getattr(m, "model", None) or getattr(m, "name", None) or str(m)
                models.append(name)

        for m in models:
            if "llama3.2" in m:
                return m
        for m in models:
            if "llama" in m:
                return m
        for m in models:
            if "embed" not in m and m:
                return m
        if models and models[0]:
            return models[0]
    except Exception:
        pass
    return default_model


def generate_answer(prompt: str, model: Optional[str] = None) -> str:
    """
    Generate an answer using Ollama LLM.
    """
    if not model:
        model = get_preferred_model()

    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response.get("response", "")
    except Exception as e:
        return f"Error communicating with Ollama model '{model}': {str(e)}"

