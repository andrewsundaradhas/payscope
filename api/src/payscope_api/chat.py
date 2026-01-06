"""
Enhanced chatbot API with advanced query support.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException

from payscope_api.security.auth import get_request_context
from payscope_api.security.context import RequestContext

logger = logging.getLogger(__name__)


async def handle_chat_query(
    query: str,
    context: RequestContext = Depends(get_request_context),
    query_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle chat query with support for why/compare/what-if queries.
    
    Args:
        query: Natural language query
        context: Request context (contains bank_id)
        query_type: Optional query type hint ("why", "compare", "what_if")
    
    Returns:
        Chat response
    """
    try:
        # Import RAG engine and advanced query handler
        from payscope_processing.rag.engine import RAGEngine
        from payscope_processing.rag.advanced_queries import AdvancedQueryHandler
        from payscope_processing.config import get_settings

        settings = get_settings()
        rag_engine = RAGEngine(settings)
        query_handler = AdvancedQueryHandler(rag_engine)

        # Detect query type if not provided
        if not query_type:
            query_lower = query.lower()
            if "why" in query_lower or "reason" in query_lower:
                query_type = "why"
            elif "compare" in query_lower:
                query_type = "compare"
            elif "what if" in query_lower or "what-if" in query_lower:
                query_type = "what_if"
            else:
                query_type = "standard"

        # Route to appropriate handler
        if query_type == "why":
            response = query_handler.handle_why_query(
                query,
                context.bank_id,
            )
        elif query_type == "compare":
            response = query_handler.handle_compare_query(
                query,
                context.bank_id,
            )
        elif query_type == "what_if":
            response = query_handler.handle_what_if_query(
                query,
                context.bank_id,
            )
        else:
            # Standard query
            response = rag_engine.query(query, bank_id=context.bank_id)

        return {
            "query": query,
            "query_type": query_type,
            "answer": response.answer,
            "explanation": getattr(response, "explanation", None),
            "sources": response.sources,
            "metrics": response.metrics,
            "confidence": response.confidence,
            "bank_id": context.bank_id,
        }

    except Exception as e:
        logger.exception("Chat query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


async def handle_dashboard_generation(
    report_ids: list[str],
    context: RequestContext = Depends(get_request_context),
    metrics: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Generate AI-powered dashboard.
    
    Args:
        report_ids: List of report IDs
        context: Request context
        metrics: Optional specific metrics
    
    Returns:
        Dashboard configuration
    """
    try:
        from payscope_processing.dashboard.generator import DashboardGenerator
        from payscope_processing.rag.engine import RAGEngine
        from payscope_processing.config import get_settings

        settings = get_settings()
        rag_engine = RAGEngine(settings)
        generator = DashboardGenerator(rag_engine)

        dashboard = generator.generate_dashboard(
            report_ids=report_ids,
            bank_id=context.bank_id,
            metrics=metrics,
        )

        return dashboard

    except Exception as e:
        logger.exception("Dashboard generation failed")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")
