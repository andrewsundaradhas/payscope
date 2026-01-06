from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as dtparser

from payscope_processing.normalize.iso4217 import CODES as ISO4217_CODES
from payscope_processing.normalize.schema import ValidationErrorItem


def parse_amount(value: Any, *, field: str, row_ref: dict[str, Any]) -> tuple[Decimal | None, list[ValidationErrorItem]]:
    errs: list[ValidationErrorItem] = []
    if value is None:
        errs.append(_err("amount_missing", "Amount is missing", field=field, row_ref=row_ref))
        return None, errs
    s = str(value).strip()
    if not s:
        errs.append(_err("amount_missing", "Amount is missing", field=field, row_ref=row_ref))
        return None, errs
    # Remove common formatting
    s2 = s.replace(",", "").replace("$", "").strip()
    # Parentheses for negative
    if s2.startswith("(") and s2.endswith(")"):
        s2 = "-" + s2[1:-1].strip()
    try:
        d = Decimal(s2)
    except (InvalidOperation, ValueError):
        errs.append(_err("amount_invalid", "Amount is not numeric", field=field, raw_value=s, row_ref=row_ref))
        return None, errs
    # Reject NaN / infinities
    if d.is_nan() or d.is_infinite():
        errs.append(_err("amount_invalid", "Amount is NaN/Infinite", field=field, raw_value=s, row_ref=row_ref))
        return None, errs
    return d, errs


def validate_currency(value: Any, *, field: str, row_ref: dict[str, Any]) -> tuple[str | None, list[ValidationErrorItem]]:
    errs: list[ValidationErrorItem] = []
    if value is None:
        errs.append(_err("currency_missing", "Currency is missing", field=field, row_ref=row_ref))
        return None, errs
    cur = str(value).strip().upper()
    if not cur:
        errs.append(_err("currency_missing", "Currency is missing", field=field, row_ref=row_ref))
        return None, errs
    if cur not in ISO4217_CODES:
        errs.append(_err("currency_invalid", "Currency is not valid ISO-4217", field=field, raw_value=cur, row_ref=row_ref))
        return None, errs
    return cur, errs


def parse_timestamp_to_utc(value: Any, *, field: str, row_ref: dict[str, Any]) -> tuple[datetime | None, list[ValidationErrorItem]]:
    errs: list[ValidationErrorItem] = []
    if value is None:
        errs.append(_err("timestamp_missing", "Timestamp is missing", field=field, row_ref=row_ref))
        return None, errs
    s = str(value).strip()
    if not s:
        errs.append(_err("timestamp_missing", "Timestamp is missing", field=field, row_ref=row_ref))
        return None, errs
    try:
        dt = dtparser.parse(s)
    except Exception:
        errs.append(_err("timestamp_invalid", "Timestamp cannot be parsed", field=field, raw_value=s, row_ref=row_ref))
        return None, errs
    # If timezone missing, treat as UTC (documented deterministic behavior).
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc, errs


def clamp01(x: float) -> float:
    if x is None:
        return 0.0
    if isinstance(x, float) and math.isnan(x):
        return 0.0
    return 0.0 if x < 0 else 1.0 if x > 1 else float(x)


def dedupe_transactions(transactions, *, key_fields: tuple[str, str] = ("transaction_id", "lifecycle_stage")):
    """
    Deduplicate deterministically by (transaction_id, lifecycle_stage):
      - keep the record with highest confidence_score
      - stable tie-breaker by lexical order of raw_source_ref.object_key + row pointer
    """
    best: dict[tuple[str, str], Any] = {}

    def tiebreak(t) -> str:
        ref = t.raw_source_ref
        parts = [
            ref.object_key,
            str(ref.page_number or ""),
            str(ref.sheet_name or ""),
            str(ref.source_row_number or ""),
            str(ref.element_id or ""),
        ]
        return "|".join(parts)

    for t in transactions:
        k = (t.transaction_id, str(t.lifecycle_stage.value if hasattr(t.lifecycle_stage, "value") else t.lifecycle_stage))
        cur = best.get(k)
        if cur is None:
            best[k] = t
            continue
        if t.confidence_score > cur.confidence_score:
            best[k] = t
        elif t.confidence_score == cur.confidence_score:
            if tiebreak(t) < tiebreak(cur):
                best[k] = t

    out = list(best.values())
    out.sort(key=lambda x: (x.transaction_id, str(x.lifecycle_stage), x.confidence_score), reverse=False)
    return out


def _err(code: str, message: str, *, field: str | None = None, raw_value: str | None = None, row_ref: dict[str, Any] | None = None) -> ValidationErrorItem:
    return ValidationErrorItem(code=code, message=message, field=field, raw_value=raw_value, row_ref=row_ref or {})




