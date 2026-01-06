from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any


class RAGResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: str
    numbers: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)




