from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserSettingsModel(BaseModel):
    chunk_size: int = Field(default=512, ge=128, le=2048)
    chunk_overlap: int = Field(default=64, ge=0, le=256)
    top_k: int = Field(default=5, ge=1, le=20)
    min_relevance_score: float = Field(default=0.30, ge=0.0, le=1.0)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    hybrid_enabled: bool = True
    reranker_enabled: bool = True
    preset_name: str = "balanced"
    updated_at: Optional[str] = None


class PresetApplyRequest(BaseModel):
    preset_name: str = Field(pattern="^(strict|balanced|deep)$")


RAG_PRESETS: Dict[str, Dict[str, Any]] = {
    "strict": {
        "chunk_size": 384,
        "chunk_overlap": 48,
        "top_k": 4,
        "min_relevance_score": 0.45,
        "temperature": 0.0,
        "hybrid_enabled": True,
        "reranker_enabled": True,
        "preset_name": "strict",
    },
    "balanced": {
        "chunk_size": 512,
        "chunk_overlap": 64,
        "top_k": 5,
        "min_relevance_score": 0.30,
        "temperature": 0.1,
        "hybrid_enabled": True,
        "reranker_enabled": True,
        "preset_name": "balanced",
    },
    "deep": {
        "chunk_size": 768,
        "chunk_overlap": 96,
        "top_k": 8,
        "min_relevance_score": 0.20,
        "temperature": 0.3,
        "hybrid_enabled": True,
        "reranker_enabled": True,
        "preset_name": "deep",
    },
}
