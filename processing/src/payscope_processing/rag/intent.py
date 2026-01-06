from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Any

from payscope_processing.config import Settings
from payscope_processing.llm.client import LlmConfig, chat_json


INTENTS = ["DESCRIPTIVE", "COMPARISON", "FORECAST", "WHAT_IF_SIMULATION"]


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float


def classify_intent(settings: Settings, query: str) -> IntentResult:
    """
    LLM-based intent classification with deterministic params and a fallback rule-based prior.
    """
    # Fallback priors (not keyword-only; uses simple heuristics weighted into final confidence)
    prior: Dict[str, float] = {k: 0.0 for k in INTENTS}
    q_lower = query.lower()
    if "forecast" in q_lower or "predict" in q_lower or "trend" in q_lower:
        prior["FORECAST"] = 0.4
    if "compare" in q_lower or "vs" in q_lower:
        prior["COMPARISON"] = max(prior["COMPARISON"], 0.3)
    if "what if" in q_lower or "scenario" in q_lower:
        prior["WHAT_IF_SIMULATION"] = max(prior["WHAT_IF_SIMULATION"], 0.4)
    if all(v == 0 for v in prior.values()):
        prior["DESCRIPTIVE"] = 0.2

    # Check if LLM is configured (either OpenAI-compatible API or free LLM)
    provider = settings.llm_provider or "openai"
    has_openai_config = settings.llm_base_url and settings.llm_api_key
    has_free_llm_config = (
        provider in ("hf", "local", "auto") or
        settings.hf_api_token or
        os.getenv("HF_API_TOKEN") or
        os.getenv("LLM_PROVIDER") in ("hf", "local", "auto")
    )
    
    if not has_openai_config and not has_free_llm_config:
        # No LLM configured; return best prior deterministically
        best = max(prior.items(), key=lambda x: x[1])
        return IntentResult(intent=best[0], confidence=best[1] if best[1] > 0 else 0.5)

    cfg = LlmConfig(
        base_url=settings.llm_base_url or "",
        api_key=settings.llm_api_key or "",
        model=settings.llm_model,
        timeout_s=settings.llm_timeout_s,
        llm_provider=settings.llm_provider,
        hf_api_token=settings.hf_api_token,
        llm_local_provider=settings.llm_local_provider,
        llm_local_base_url=settings.llm_local_base_url,
        llm_local_model=settings.llm_local_model,
    )

    system = "Classify the user intent for a payment analytics question into one of: DESCRIPTIVE, COMPARISON, FORECAST, WHAT_IF_SIMULATION. Return JSON only with {intent, confidence}."
    user = f"Query: {query}\nReturn JSON."
    schema = {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": INTENTS},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["intent", "confidence"],
        "additionalProperties": False,
    }

    raw = chat_json(cfg=cfg, system=system, user=user, response_json_schema=schema)
    try:
        intent = raw["intent"]
        conf = float(raw["confidence"])
    except Exception:
        intent = "DESCRIPTIVE"
        conf = 0.5

    # Blend LLM confidence with prior (deterministic, convex combination)
    prior_boost = prior.get(intent, 0.0)
    final_conf = min(1.0, 0.7 * conf + 0.3 * prior_boost)
    return IntentResult(intent=intent, confidence=final_conf)


