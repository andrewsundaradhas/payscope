"""
Chat API request/response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")


class ChatFilters(BaseModel):
    """Chat filters schema."""
    network: Optional[str] = Field("All", description="Network filter (Visa, Mastercard, All)")
    range_days: Optional[int] = Field(30, description="Date range in days")


class ChatQueryRequest(BaseModel):
    """Chat query request schema - matches frontend sendChatQuery()."""
    report_id: str = Field(..., description="Report ID to query against")
    question: str = Field(..., description="Natural language question")
    filters: Optional[ChatFilters] = Field(default_factory=ChatFilters, description="Query filters")
    thread: Optional[List[ChatMessage]] = Field(default_factory=list, description="Conversation history")


class ChatMetric(BaseModel):
    """Chat metric schema."""
    label: str = Field(..., description="Metric label")
    value: str = Field(..., description="Metric value")


class ChatQueryResponse(BaseModel):
    """Chat query response schema - matches frontend ChatApiResponse."""
    answer: str = Field(..., description="Human-readable answer")
    metrics_used: List[ChatMetric] = Field(default_factory=list, description="Metrics referenced")
    followups: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[str] = Field(default_factory=list, description="Sources/agents used")



