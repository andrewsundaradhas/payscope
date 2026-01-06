from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are a payments data normalization engine.
Your job: map unknown, vendor-specific extracted fields into a canonical payment schema.
You must be conservative, explainable, and deterministic.

Rules:
- Do NOT assume vendor column names are meaningful.
- Use the provided sample values, inferred types, and context.
- Output MUST be valid JSON matching the provided schema.
- Only use lifecycle_stage values: AUTH, CLEARING, SETTLEMENT.
- Confidence scores are 0..1. Use low confidence when uncertain.
"""


def build_user_prompt(payload: dict[str, Any]) -> str:
    """
    Payload should include:
      - artifact_id, source_network (if known)
      - report_context: list of representative strings from the document
      - columns: list of {raw_field, sample_values, inferred_type}
      - required_canonical_fields list
    """
    return (
        "Map the following extracted fields into canonical fields.\n\n"
        f"INPUT:\n{payload}\n\n"
        "Return only JSON."
    )


def response_schema() -> dict[str, Any]:
    # JSON Schema enforcing the required output contract
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "lifecycle": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "lifecycle_stage": {"type": "string", "enum": ["AUTH", "CLEARING", "SETTLEMENT"]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "mapping_rationale": {"type": "string"},
                },
                "required": ["lifecycle_stage", "confidence_score", "mapping_rationale"],
            },
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "raw_field": {"type": "string"},
                        "canonical_field": {"type": "string"},
                        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "mapping_rationale": {"type": "string"},
                    },
                    "required": ["raw_field", "canonical_field", "confidence_score", "mapping_rationale"],
                },
            },
        },
        "required": ["lifecycle", "mappings"],
    }




