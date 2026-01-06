from __future__ import annotations

from typing import Any

from payscope_processing.config import Settings
from payscope_processing.llm.client import LlmConfig, chat_json
from payscope_processing.llm.mapping_prompt import SYSTEM_PROMPT, build_user_prompt, response_schema
from payscope_processing.normalize.schema import LlmMappingResponse


class MappingRejected(RuntimeError):
    pass


def infer_mapping_via_llm(
    *,
    settings: Settings,
    artifact_id: str,
    report_context: list[str],
    columns: list[dict[str, Any]],
    required_canonical_fields: list[str],
) -> LlmMappingResponse:
    if not settings.llm_base_url or not settings.llm_api_key:
        raise MappingRejected("llm_not_configured (LLM_BASE_URL/LLM_API_KEY required)")

    payload = {
        "artifact_id": artifact_id,
        "report_context": report_context[:50],
        "columns": columns[:200],
        "required_canonical_fields": required_canonical_fields,
        "notes": [
            "No hardcoded column assumptions.",
            "Return confidence per mapping; reject/omit low-confidence mappings.",
        ],
    }

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

    raw = chat_json(cfg=cfg, system=SYSTEM_PROMPT, user=build_user_prompt(payload), response_json_schema=response_schema())
    resp = LlmMappingResponse.model_validate(raw)

    # Confidence thresholding: drop mappings below threshold (soft-fail).
    thr = float(settings.mapping_confidence_threshold)
    resp.mappings = [m for m in resp.mappings if m.confidence_score >= thr]
    if resp.lifecycle.confidence_score < thr:
        raise MappingRejected("lifecycle_inference_below_threshold")

    return resp


