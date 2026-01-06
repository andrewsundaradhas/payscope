"""
Intent mapping between existing intents and required intent names.
"""

from __future__ import annotations

# Mapping from existing intent names to required intent names
INTENT_MAPPING = {
    "DESCRIPTIVE": "DESCRIBE",
    "COMPARISON": "COMPARE",
    "FORECAST": "FORECAST",
    "WHAT_IF_SIMULATION": "WHAT_IF",
}

# Reverse mapping for compatibility
REVERSE_INTENT_MAPPING = {v: k for k, v in INTENT_MAPPING.items()}

# Required intents
REQUIRED_INTENTS = ["DESCRIBE", "COMPARE", "ANOMALY", "FORECAST", "WHAT_IF"]


def map_intent_to_required(intent: str) -> str:
    """
    Map existing intent name to required intent name.
    
    Args:
        intent: Existing intent name (DESCRIPTIVE, COMPARISON, etc.)
    
    Returns:
        Required intent name (DESCRIBE, COMPARE, etc.)
    """
    return INTENT_MAPPING.get(intent, intent)


def map_intent_to_existing(intent: str) -> str:
    """
    Map required intent name to existing intent name.
    
    Args:
        intent: Required intent name (DESCRIBE, COMPARE, etc.)
    
    Returns:
        Existing intent name (DESCRIPTIVE, COMPARISON, etc.)
    """
    return REVERSE_INTENT_MAPPING.get(intent, intent)



