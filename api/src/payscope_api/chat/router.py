"""
Chat query router - /chat/query endpoint.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header

from payscope_api.chat.schemas import ChatQueryRequest, ChatQueryResponse, ChatMetric
from payscope_api.chat.intent_mapper import map_intent_to_existing

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)


def _detect_intent(question: str) -> str:
    """Detect intent from question text."""
    q = question.lower()
    if "why" in q or "reason" in q or "cause" in q:
        return "WHY"
    elif "compare" in q or "vs" in q or "versus" in q:
        return "COMPARE"
    elif "forecast" in q or "predict" in q or "next" in q:
        return "FORECAST"
    elif "what if" in q or "what-if" in q or "simulate" in q:
        return "WHAT_IF"
    elif "chargeback" in q:
        return "CHARGEBACK"
    elif "decline" in q:
        return "DECLINE"
    elif "settlement" in q and ("drop" in q or "decrease" in q):
        return "SETTLEMENT_DROP"
    else:
        return "DESCRIBE"


def _get_agents_for_intent(intent: str) -> List[str]:
    """Get agents to invoke for a given intent."""
    if intent in ("WHY", "SETTLEMENT_DROP"):
        return ["AnalyticsAgent", "ReconciliationAgent"]
    elif intent == "COMPARE":
        return ["ReconciliationAgent", "ComparisonAgent"]
    elif intent == "FORECAST":
        return ["ForecastingAgent"]
    elif intent == "WHAT_IF":
        return ["SimulationAgent"]
    elif intent == "CHARGEBACK":
        return ["FraudAgent", "ComplianceAgent"]
    elif intent == "DECLINE":
        return ["FraudAgent", "ReconciliationAgent"]
    else:
        return ["ReconciliationAgent"]


def _generate_mock_response(question: str, intent: str, report_id: str) -> Dict[str, Any]:
    """Generate a mock response when RAG engine is unavailable."""
    q = question.lower()
    
    if "settlement" in q and ("drop" in q or "decrease" in q):
        return {
            "answer": (
                "Looking at the settlement data, there appears to be a decrease in settlement volume. "
                "This could be attributed to several factors:\n\n"
                "1) **Cross-border mix changes**: Cross-border transactions may have shifted, affecting overall settlement timing.\n"
                "2) **Timing variations**: Settlement delays can shift recognized volume across reporting periods.\n"
                "3) **Network-specific patterns**: Visa and Mastercard may have different settlement cycles.\n\n"
                "Would you like me to break this down by merchant or analyze the cross-border vs domestic split?"
            ),
            "metrics_used": [
                {"label": "Settlement Period", "value": "Last 7 days"},
                {"label": "Analysis Type", "value": "Trend Analysis"},
            ],
            "followups": [
                "Break down settlement by merchant",
                "Compare cross-border vs domestic volume",
                "Show settlement timing patterns",
            ],
            "confidence": 0.85,
        }
    elif "compare" in q and ("visa" in q or "mastercard" in q):
        return {
            "answer": (
                "Comparing Visa vs Mastercard performance:\n\n"
                "**Approval Rates**: Both networks show similar approval patterns, though Visa typically "
                "has slightly higher approval rates due to broader issuer support.\n\n"
                "**Settlement**: Settlement timing varies by network, with Mastercard often settling slightly faster.\n\n"
                "**Interchange**: Fee structures differ, with variations based on transaction type and merchant category."
            ),
            "metrics_used": [
                {"label": "Networks Compared", "value": "Visa, Mastercard"},
                {"label": "Comparison Type", "value": "Multi-metric"},
            ],
            "followups": [
                "Show approval rate by hour",
                "Compare interchange fees by network",
                "Which merchants have the biggest network gap?",
            ],
            "confidence": 0.82,
        }
    elif "chargeback" in q:
        return {
            "answer": (
                "Analyzing chargeback patterns:\n\n"
                "Chargebacks are typically concentrated among a few merchants with higher-risk profiles. "
                "Key factors include:\n\n"
                "- **Entry mode**: E-commerce transactions have higher chargeback rates than card-present.\n"
                "- **Merchant category**: Certain MCCs (like digital goods) have elevated risk.\n"
                "- **Cross-border**: International transactions show higher dispute rates.\n\n"
                "To prioritize investigations, I recommend normalizing by volume (chargebacks per 10k transactions)."
            ),
            "metrics_used": [
                {"label": "Analysis Focus", "value": "Chargeback Distribution"},
            ],
            "followups": [
                "Show chargeback rate by merchant",
                "Segment by entry mode",
                "Are cross-border chargebacks higher?",
            ],
            "confidence": 0.80,
        }
    elif "forecast" in q or "predict" in q:
        return {
            "answer": (
                "Based on historical patterns and current trends:\n\n"
                "**Volume Forecast**: Transaction volume is projected to remain stable with slight growth.\n"
                "**Seasonal Factors**: Expect increased activity around month-end settlement cycles.\n"
                "**Risk Outlook**: Decline rates should remain within normal parameters.\n\n"
                "Note: Forecasts are based on available historical data and may vary with market conditions."
            ),
            "metrics_used": [
                {"label": "Forecast Horizon", "value": "30 days"},
                {"label": "Confidence Interval", "value": "95%"},
            ],
            "followups": [
                "Show forecast breakdown by network",
                "What factors could change this forecast?",
                "Compare to last month's actual",
            ],
            "confidence": 0.75,
        }
    else:
        return {
            "answer": (
                f"Analyzing your query about the selected report:\n\n"
                "Based on the available data, I can provide insights on:\n"
                "- **Authorization performance**: Approval rates and decline patterns\n"
                "- **Settlement metrics**: Volume, interchange, and timing\n"
                "- **Risk indicators**: Chargeback and fraud patterns\n\n"
                "Please ask a more specific question, such as:\n"
                "- 'Why did settlement drop last week?'\n"
                "- 'Compare Visa vs Mastercard approval rates'\n"
                "- 'Which merchants have the highest chargebacks?'"
            ),
            "metrics_used": [
                {"label": "Report ID", "value": report_id[:8] + "..." if len(report_id) > 8 else report_id},
            ],
            "followups": [
                "Why did settlement drop last week?",
                "Compare Visa vs Mastercard approval rates",
                "Show decline patterns by hour",
            ],
            "confidence": 0.70,
        }


@router.post("/query")
async def chat_query(request: ChatQueryRequest) -> ChatQueryResponse:
    """
    Analytical chatbot query endpoint.
    
    Accepts natural language questions about payment reports and returns
    AI-generated insights using Llama via RAG pipeline.
    """
    try:
        # Detect intent from the question
        intent = _detect_intent(request.question)
        agents_invoked = _get_agents_for_intent(intent)
        
        # Try to use RAG engine with Llama
        try:
            from payscope_processing.rag.engine import RAGEngine
            from payscope_processing.config import get_settings
            
            settings = get_settings()
            rag_engine = RAGEngine(settings)
            
            # Prepare filters
            filters: Dict[str, Any] = {
                "report_id": request.report_id,
            }
            if request.filters:
                if request.filters.network:
                    filters["network"] = request.filters.network
                if request.filters.range_days:
                    filters["range_days"] = request.filters.range_days
            
            # Add conversation context
            if request.thread:
                filters["thread"] = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.thread
                ]
            
            # Execute query via RAG engine
            response = rag_engine.run(request.question, filters=filters)
            
            # Extract metrics
            raw_metrics = response.get("metrics", response.get("numbers", {}))
            metrics_used = [
                ChatMetric(label=k, value=str(v))
                for k, v in raw_metrics.items()
                if k != "forecast"
            ]
            
            # Build response
            answer = response.get("answer", response.get("explanation", "No response generated."))
            followups = response.get("followups", response.get("suggested_questions", []))
            confidence = response.get("confidence", 0.75)
            
            logger.info(
                f"Chat query processed via RAG: intent={intent}, report_id={request.report_id}",
                extra={
                    "intent": intent,
                    "agents_invoked": agents_invoked,
                    "confidence": confidence,
                },
            )
            
            return ChatQueryResponse(
                answer=answer,
                metrics_used=metrics_used,
                followups=followups if isinstance(followups, list) else [],
                intent=intent,
                confidence=confidence,
                sources=agents_invoked,
            )
            
        except ImportError as e:
            logger.warning(f"RAG engine not available: {e}. Using mock responses.")
            # Fall through to mock response
        except Exception as e:
            logger.warning(f"RAG engine error: {e}. Using mock responses.")
            # Fall through to mock response
        
        # Generate mock response when RAG is unavailable
        mock = _generate_mock_response(request.question, intent, request.report_id)
        
        logger.info(
            f"Chat query processed (mock): intent={intent}, report_id={request.report_id}",
            extra={
                "intent": intent,
                "agents_invoked": agents_invoked,
                "mock": True,
            },
        )
        
        return ChatQueryResponse(
            answer=mock["answer"],
            metrics_used=[ChatMetric(**m) for m in mock["metrics_used"]],
            followups=mock["followups"],
            intent=intent,
            confidence=mock["confidence"],
            sources=agents_invoked,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Chat query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")



