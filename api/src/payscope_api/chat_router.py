"""
Chat API router for natural language queries.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from payscope_api.chat import handle_chat_query, handle_dashboard_generation
from payscope_api.security.auth import get_request_context
from payscope_api.security.context import RequestContext

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    query_type: str | None = None


class DashboardRequest(BaseModel):
    report_ids: list[str]
    metrics: list[str] | None = None


@router.post("")
async def chat(
    request: ChatRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    """Natural language chat query with support for why/compare/what-if queries."""
    return await handle_chat_query(request.query, ctx, request.query_type)


@router.post("/dashboard/generate")
async def generate_dashboard(
    request: DashboardRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict:
    """Generate AI-powered dashboard."""
    return await handle_dashboard_generation(request.report_ids, ctx, request.metrics)



