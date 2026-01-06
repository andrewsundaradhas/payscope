from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


EventType = Literal["INGEST", "AGENT_DECISION", "FORECAST"]


class LedgerEvent(BaseModel):
    """
    On-chain payload (hashed artifacts only).
    """

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: EventType
    artifact_hash: str = Field(min_length=64, max_length=64)
    schema_version: str
    timestamp: datetime

    @field_validator("artifact_hash")
    @classmethod
    def _is_hex_sha256(cls, v: str) -> str:
        s = v.lower()
        if len(s) != 64:
            raise ValueError("artifact_hash must be sha256 hex (64 chars)")
        int(s, 16)  # will raise if not hex
        return s

    @field_validator("timestamp")
    @classmethod
    def _ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class AuditableEventLog(BaseModel):
    """
    Off-chain auditable log record referencing Fabric tx id.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    component: Literal["agent", "model", "pipeline"]
    hash: str
    confidence: float = Field(ge=0.0, le=1.0)
    ledger_tx_id: str
    timestamp: datetime




