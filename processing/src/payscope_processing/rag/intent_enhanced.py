"""
Enhanced intent classification with ANOMALY intent support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from payscope_processing.config import Settings
from payscope_processing.rag.intent import IntentResult, classify_intent as base_classify_intent

# Required intents (matching requirements)
REQUIRED_INTENTS = ["DESCRIBE", "COMPARE", "ANOMALY", "FORECAST", "WHAT_IF"]


@dataclass(frozen=True)
class EnhancedIntentResult:
    """Enhanced intent result with required intent names."""
    intent: str  # Required intent name (DESCRIBE, COMPARE, ANOMALY, etc.)
    confidence: float
    original_intent: str  # Original intent name (for compatibility)


def classify_intent_enhanced(settings: Settings, query: str) -> EnhancedIntentResult:
    """
    Enhanced intent classification with ANOMALY support.
    
    Adds ANOMALY detection and maps existing intents to required names.
    """
    q_lower = query.lower()
    
    # Check for ANOMALY intent first (fraud, anomaly, suspicious, spike, unusual)
    anomaly_keywords = ["fraud", "anomaly", "anomalies", "suspicious", "spike", "unusual", "irregular", "abnormal"]
    if any(keyword in q_lower for keyword in anomaly_keywords):
        # Check if it's actually a comparison (e.g., "compare fraud rates")
        if "compare" in q_lower or "vs" in q_lower or "versus" in q_lower:
            # Route to COMPARE
            base_result = base_classify_intent(settings, query)
            return EnhancedIntentResult(
                intent="COMPARE",
                confidence=base_result.confidence,
                original_intent=base_result.intent,
            )
        # Otherwise, route to ANOMALY
        return EnhancedIntentResult(
            intent="ANOMALY",
            confidence=0.8,  # High confidence for explicit anomaly keywords
            original_intent="ANOMALY",
        )
    
    # Use existing classifier for other intents
    base_result = base_classify_intent(settings, query)
    
    # Map existing intents to required intents
    intent_mapping = {
        "DESCRIPTIVE": "DESCRIBE",
        "COMPARISON": "COMPARE",
        "FORECAST": "FORECAST",
        "WHAT_IF_SIMULATION": "WHAT_IF",
    }
    
    required_intent = intent_mapping.get(base_result.intent, base_result.intent)
    
    return EnhancedIntentResult(
        intent=required_intent,
        confidence=base_result.confidence,
        original_intent=base_result.intent,
    )



