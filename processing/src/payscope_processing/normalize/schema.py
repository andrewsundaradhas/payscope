from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


SCHEMA_VERSION = "1.0.0"


class LifecycleStage(str, Enum):
    AUTH = "AUTH"
    CLEARING = "CLEARING"
    SETTLEMENT = "SETTLEMENT"


class RawSourceRef(BaseModel):
    """
    Traceability to original raw extraction (no UI concerns).
    """

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    object_key: str
    # Lineage pointers (optional; populated where applicable)
    source_type: Literal["pdf_element", "csv_row", "xlsx_row"]
    page_number: int | None = None
    element_id: str | None = None
    sheet_name: str | None = None
    source_row_number: int | None = None
    raw_fields_used: list[str] = Field(default_factory=list)


class TransactionFact(BaseModel):
    """
    Canonical, schema-agnostic transaction fact.

    Forward-compatibility strategy:
      - keep a strict core model (extra=forbid)
      - allow new fields via `extensions` without changing the core contract
    """

    model_config = ConfigDict(extra="forbid")

    transaction_id: str
    amount: Decimal
    currency: str  # ISO-4217
    timestamp_utc: datetime
    lifecycle_stage: LifecycleStage
    merchant_id: str
    card_network: str
    raw_source_ref: RawSourceRef
    confidence_score: float = Field(ge=0.0, le=1.0)

    extensions: dict[str, Any] = Field(default_factory=dict)


class ReportFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    report_type: str
    ingestion_time: datetime
    source_network: str
    record_count: int = Field(ge=0)
    schema_version: str = SCHEMA_VERSION

    extensions: dict[str, Any] = Field(default_factory=dict)


class MappingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_field: str
    canonical_field: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    mapping_rationale: str


class LifecycleInference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lifecycle_stage: LifecycleStage
    confidence_score: float = Field(ge=0.0, le=1.0)
    mapping_rationale: str


class LlmMappingResponse(BaseModel):
    """
    Contract enforced on LLM output.
    """

    model_config = ConfigDict(extra="forbid")

    lifecycle: LifecycleInference
    mappings: list[MappingDecision]


class ValidationErrorItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None
    raw_value: str | None = None
    row_ref: dict[str, Any] = Field(default_factory=dict)


class NormalizationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    report_fact: ReportFact
    transactions: list[TransactionFact]
    mapping: LlmMappingResponse | None = None
    errors: list[ValidationErrorItem] = Field(default_factory=list)




