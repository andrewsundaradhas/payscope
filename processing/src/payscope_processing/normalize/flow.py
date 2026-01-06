from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from payscope_processing.contracts import IntermediateDocument, LayoutUnderstandingOutput
from payscope_processing.normalize.llm_mapper import MappingRejected, infer_mapping_via_llm
from payscope_processing.normalize.schema import (
    LifecycleStage,
    NormalizationResult,
    RawSourceRef,
    ReportFact,
    TransactionFact,
    ValidationErrorItem,
)
from payscope_processing.normalize.validate import (
    clamp01,
    dedupe_transactions,
    parse_amount,
    parse_timestamp_to_utc,
    validate_currency,
)


REQUIRED_CANONICAL_FIELDS = [
    "transaction_id",
    "amount",
    "currency",
    "timestamp_utc",
    "merchant_id",
    "card_network",
]


def normalize_tabular(
    *,
    settings,
    bank_id: str,
    artifact_id: str,
    report_id: str,
    report_type: str,
    ingestion_time: datetime,
    source_network: str,
    source_object_key: str,
    tabular_json: dict[str, Any],
) -> NormalizationResult:
    """
    Tabular normalization:
      - LLM infers lifecycle_stage + mapping from raw columns -> canonical fields (no hardcoded raw column names)
      - validation enforces financial primitives
      - dedupe by (transaction_id, lifecycle_stage)
    """
    errors: list[ValidationErrorItem] = []

    # Build mapping inputs: columns + representative values
    # Use first table for mapping; mapping applies across all tables deterministically.
    tables = tabular_json.get("tables", [])
    if not tables:
        rf = _report_fact(report_id, report_type, ingestion_time, source_network, 0)
        errors.append(ValidationErrorItem(code="no_tables", message="No tabular tables found", row_ref={}))
        return NormalizationResult(artifact_id=artifact_id, report_fact=rf, transactions=[], mapping=None, errors=errors)

    first = tables[0]
    norm_cols = first.get("columns_normalized") or []
    orig_cols = first.get("columns_original") or []
    norm_to_orig: dict[str, str] = {}
    for i, n in enumerate(norm_cols):
        try:
            norm_to_orig[n] = str(orig_cols[i])
        except Exception:
            norm_to_orig[n] = n
    sample_rows = first.get("rows") or []
    # Derive sample values per column
    samples: dict[str, list[str]] = {c: [] for c in norm_cols}
    for r in sample_rows[:25]:
        vals = r.get("values", {})
        for c in norm_cols:
            v = vals.get(c)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                samples[c].append(s[:80])

    columns = []
    for c in norm_cols:
        sv = samples.get(c, [])[:8]
        inferred_type = _infer_type(sv)
        columns.append(
            {
                "raw_field": c,
                "raw_field_original": norm_to_orig.get(c, c),
                "sample_values": sv,
                "inferred_type": inferred_type,
            }
        )

    # Report context: light strings for LLM (no schema assumptions)
    report_context = []
    for c in norm_cols[:30]:
        report_context.append(f"column: {c}")

    mapping = None
    lifecycle = LifecycleStage.AUTH
    try:
        mapping = infer_mapping_via_llm(
            settings=settings,
            artifact_id=artifact_id,
            report_context=report_context,
            columns=columns,
            required_canonical_fields=REQUIRED_CANONICAL_FIELDS + ["lifecycle_stage"],
        )
        lifecycle = mapping.lifecycle.lifecycle_stage
    except MappingRejected as e:
        errors.append(ValidationErrorItem(code="mapping_rejected", message=str(e), row_ref={}))
        rf = _report_fact(report_id, report_type, ingestion_time, source_network, 0)
        return NormalizationResult(artifact_id=artifact_id, report_fact=rf, transactions=[], mapping=None, errors=errors)

    # Build raw->canonical dict
    raw_to_canon: dict[str, str] = {m.raw_field: m.canonical_field for m in mapping.mappings}
    # Preserve original header lineage in rationale deterministically
    for m in mapping.mappings:
        orig = norm_to_orig.get(m.raw_field)
        if orig and orig != m.raw_field:
            m.mapping_rationale = f"{m.mapping_rationale} (original_header={orig})"

    txs: list[TransactionFact] = []

    # Normalize across all tables/sheets
    for t in tables:
        sheet = t.get("sheet_name")
        rows = t.get("rows") or []
        for r in rows:
            row_ref = {
                "sheet_name": sheet,
                "source_row_number": r.get("source_row_number"),
            }
            values = r.get("values", {})

            # Extract canonical values
            raw_fields_used = []
            def get_by_canon(canon: str) -> Any:
                for raw_field, mapped in raw_to_canon.items():
                    if mapped == canon:
                        raw_fields_used.append(raw_field)
                        return values.get(raw_field)
                return None

            tx_id = get_by_canon("transaction_id")
            amt = get_by_canon("amount")
            cur = get_by_canon("currency")
            ts = get_by_canon("timestamp_utc")
            merch = get_by_canon("merchant_id")
            net = get_by_canon("card_network")

            # Hard-fail invalid primitives: amount/currency/timestamp
            parsed_amt, e_amt = parse_amount(amt, field="amount", row_ref=row_ref)
            parsed_cur, e_cur = validate_currency(cur, field="currency", row_ref=row_ref)
            parsed_ts, e_ts = parse_timestamp_to_utc(ts, field="timestamp_utc", row_ref=row_ref)
            if e_amt or e_cur or e_ts:
                errors.extend(e_amt + e_cur + e_ts)
                continue

            if not tx_id or not str(tx_id).strip():
                errors.append(ValidationErrorItem(code="transaction_id_missing", message="transaction_id missing", field="transaction_id", row_ref=row_ref))
                continue
            if not merch or not str(merch).strip():
                errors.append(ValidationErrorItem(code="merchant_id_missing", message="merchant_id missing", field="merchant_id", row_ref=row_ref))
                continue
            if not net or not str(net).strip():
                errors.append(ValidationErrorItem(code="card_network_missing", message="card_network missing", field="card_network", row_ref=row_ref))
                continue

            # Confidence score = average of mapping confidences used (deterministic)
            confs = []
            for m in mapping.mappings:
                if m.raw_field in raw_fields_used:
                    confs.append(m.confidence_score)
            conf = clamp01(sum(confs) / max(1, len(confs)))

            txs.append(
                TransactionFact(
                    transaction_id=str(tx_id).strip(),
                    amount=parsed_amt or Decimal("0"),
                    currency=parsed_cur or "USD",
                    timestamp_utc=parsed_ts or datetime.now(timezone.utc),
                    lifecycle_stage=lifecycle,
                    merchant_id=str(merch).strip(),
                    card_network=str(net).strip(),
                    raw_source_ref=RawSourceRef(
                        artifact_id=artifact_id,
                        object_key=source_object_key,
                        source_type="csv_row" if tabular_json.get("kind") == "csv" else "xlsx_row",
                        sheet_name=sheet,
                        source_row_number=r.get("source_row_number"),
                        raw_fields_used=raw_fields_used,
                    ),
                    confidence_score=conf,
                )
            )

    txs = dedupe_transactions(txs)
    rf = _report_fact(report_id, report_type, ingestion_time, source_network, len(txs))
    return NormalizationResult(artifact_id=artifact_id, report_fact=rf, transactions=txs, mapping=mapping, errors=errors)


def normalize_pdf_elements(
    *,
    bank_id: str,
    artifact_id: str,
    report_id: str,
    report_type: str,
    ingestion_time: datetime,
    source_network: str,
    source_object_key: str,
    intermediate: IntermediateDocument,
    layout: LayoutUnderstandingOutput | None,
) -> NormalizationResult:
    """
    PDF normalization baseline:
      - Use LayoutLMv3 element predictions to assemble candidate facts per page/row.
      - Use LLM only for lifecycle stage inference from document context (no raw column names).
    """
    errors: list[ValidationErrorItem] = []

    # Build minimal context for lifecycle inference
    ctx = [e.text for e in intermediate.elements[:80] if e.text][:50]
    mapping = None
    lifecycle = LifecycleStage.AUTH
    try:
        mapping = infer_mapping_via_llm(
            settings=settings,
            artifact_id=artifact_id,
            report_context=ctx,
            columns=[],
            required_canonical_fields=["lifecycle_stage"],
        )
        lifecycle = mapping.lifecycle.lifecycle_stage
    except Exception as e:
        errors.append(ValidationErrorItem(code="lifecycle_inference_failed", message=str(e), row_ref={}))

    if not layout:
        rf = _report_fact(report_id, report_type, ingestion_time, source_network, 0)
        errors.append(ValidationErrorItem(code="layout_missing", message="layout output missing for pdf", row_ref={}))
        return NormalizationResult(artifact_id=artifact_id, report_fact=rf, transactions=[], mapping=mapping, errors=errors)

    # Group elements by page and approximate row by y-center bins
    per_page: dict[int, list] = {}
    for el in layout.elements:
        per_page.setdefault(el.page_number, []).append(el)

    txs: list[TransactionFact] = []

    for page_number, els in per_page.items():
        # keep only elements with bbox and predictions
        els = [e for e in els if e.bounding_box and e.predictions]
        # compute y-center and bucket size
        ys = [((e.bounding_box.y1 + e.bounding_box.y2) / 2.0) for e in els]
        if not ys:
            continue
        # deterministic bucket size: median height or fallback
        heights = [(e.bounding_box.y2 - e.bounding_box.y1) for e in els if e.bounding_box]
        bucket = max(10.0, _median(heights) * 1.5 if heights else 18.0)

        rows: dict[int, list] = {}
        for e in els:
            yc = (e.bounding_box.y1 + e.bounding_box.y2) / 2.0
            key = int(yc // bucket)
            rows.setdefault(key, []).append(e)

        for _, row_els in rows.items():
            # pick best candidates by prediction
            txid = _best_text(row_els, "transaction_id")
            amt = _best_text(row_els, "amount")
            cur = _best_text(row_els, "currency")
            ts = _best_text(row_els, "date")  # map date -> timestamp_utc
            status = _best_text(row_els, "status")

            # Minimal required fields; merchant/network may not exist in PDF rows (soft fail)
            row_ref = {"page_number": page_number}
            if not txid:
                continue

            parsed_amt, e_amt = parse_amount(amt, field="amount", row_ref=row_ref)
            parsed_cur, e_cur = validate_currency(cur, field="currency", row_ref=row_ref)
            parsed_ts, e_ts = parse_timestamp_to_utc(ts, field="timestamp_utc", row_ref=row_ref)
            if e_amt or e_cur or e_ts:
                errors.extend(e_amt + e_cur + e_ts)
                continue

            # Use document-level network (source_network) as card_network baseline for PDF
            # (deterministic; preserves traceability)
            card_network = source_network or "UNKNOWN"
            merchant_id = "UNKNOWN"

            conf = _row_confidence(row_els)

            txs.append(
                TransactionFact(
                    transaction_id=txid,
                    amount=parsed_amt or Decimal("0"),
                    currency=parsed_cur or "USD",
                    timestamp_utc=parsed_ts or datetime.now(timezone.utc),
                    lifecycle_stage=lifecycle,
                    merchant_id=merchant_id,
                    card_network=card_network,
                    raw_source_ref=RawSourceRef(
                        artifact_id=artifact_id,
                        object_key=source_object_key,
                        source_type="pdf_element",
                        page_number=page_number,
                        element_id=row_els[0].element_id,
                        raw_fields_used=["layout_elements"],
                    ),
                    confidence_score=conf,
                    extensions={"status": status} if status else {},
                )
            )

    txs = dedupe_transactions(txs)
    rf = _report_fact(report_id, report_type, ingestion_time, source_network, len(txs))
    return NormalizationResult(artifact_id=artifact_id, report_fact=rf, transactions=txs, mapping=mapping, errors=errors)


def _infer_type(samples: list[str]) -> str:
    if not samples:
        return "unknown"
    s = " ".join(samples).lower()
    if any(ch.isdigit() for ch in s) and any(ch in s for ch in ["-", "/", ":", "t", "z"]):
        return "datetime_or_id"
    if any(ch.isdigit() for ch in s) and any(sym in s for sym in [".", ",", "$"]):
        return "numeric"
    if len(max(samples, key=len)) > 30:
        return "text"
    return "string"


def _report_fact(report_id: str, report_type: str, ingestion_time: datetime, source_network: str, record_count: int) -> ReportFact:
    return ReportFact(
        report_id=report_id,
        report_type=report_type,
        ingestion_time=ingestion_time,
        source_network=source_network,
        record_count=record_count,
    )


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    mid = len(ys) // 2
    return ys[mid] if len(ys) % 2 else (ys[mid - 1] + ys[mid]) / 2.0


def _best_text(row_els, field_type: str) -> str | None:
    best = None
    best_c = -1.0
    for e in row_els:
        for p in e.predictions:
            if p.field_type == field_type and p.confidence > best_c:
                best_c = p.confidence
                best = e.text.strip()
    return best


def _row_confidence(row_els) -> float:
    # Deterministic: average top prediction confidence per required field
    fields = ["transaction_id", "amount", "currency", "date", "status"]
    acc = 0.0
    n = 0
    for f in fields:
        best = 0.0
        for e in row_els:
            for p in e.predictions:
                if p.field_type == f and p.confidence > best:
                    best = p.confidence
        if best > 0:
            acc += best
            n += 1
    return clamp01(acc / max(1, n))


