## Phase 3 — Semantic Normalization (Canonical Payment Schema)

Objective: normalize heterogeneous vendor reports into a **canonical, machine-verifiable** schema for analytics/ML/agents.

### Canonical schema definitions

Implemented in:
- `processing/src/payscope_processing/normalize/schema.py`

Core models (strict, extra=forbid; forward-compatible via `extensions`):
- **`LifecycleStage`** enum (exact values enforced): `AUTH`, `CLEARING`, `SETTLEMENT`
- **`TransactionFact`** (minimum required fields):
  - `transaction_id`
  - `amount` (Decimal)
  - `currency` (ISO-4217)
  - `timestamp_utc` (UTC)
  - `lifecycle_stage` (enum)
  - `merchant_id`
  - `card_network`
  - `raw_source_ref` (traceability pointers)
  - `confidence_score` (0..1)
- **`ReportFact`**:
  - `report_id`
  - `report_type`
  - `ingestion_time`
  - `source_network`
  - `record_count`
  - `schema_version`

### LLM-based field mapping (explainable, reproducible)

Implemented in:
- `processing/src/payscope_processing/llm/client.py`
- `processing/src/payscope_processing/llm/mapping_prompt.py`
- `processing/src/payscope_processing/normalize/llm_mapper.py`

Architecture decisions (brief):
- LLM calls are **temperature=0** and **top_p=1** for maximum determinism.
- Output contract is enforced via a **strict JSON Schema** and then validated by Pydantic (`LlmMappingResponse`).
- Confidence thresholding is enforced server-side:
  - mappings below `MAPPING_CONFIDENCE_THRESHOLD` are **soft-failed (dropped)**
  - lifecycle inference below threshold **rejects normalization** for that artifact (soft-fail with structured error)

**Prompt contract**: includes sample values and inferred types; does **not** hardcode column names.

**Response contract** (`LlmMappingResponse`):
- `lifecycle`: `{ lifecycle_stage, confidence_score, mapping_rationale }`
- `mappings[]`: `{ raw_field, canonical_field, confidence_score, mapping_rationale }`

### Validation rules (mandatory)

Implemented in:
- `processing/src/payscope_processing/normalize/validate.py`
- `processing/src/payscope_processing/normalize/iso4217.py`

Rules:
- **Amount**: parsed to Decimal; rejects NaN/Inf/malformed values (hard-fail per row)
- **Currency**: validated against ISO-4217 allowlist (hard-fail per row)
- **Timestamp**: parsed from multiple formats; normalized to UTC (hard-fail per row if unparseable)
- **Deduplication**: deterministic by `(transaction_id, lifecycle_stage)`; keeps highest `confidence_score`
- **Idempotency**: enforced at job level (`parse_jobs` claim + output keys are deterministic)

Failures:
- **Soft-fail**: low-confidence mappings (dropped) and mapping rejection are emitted as structured errors
- **Hard-fail**: invalid primitives reject the row; validation errors are emitted

### End-to-end normalization flow

Orchestration:
- Worker: `processing/src/payscope_processing/tasks.py` (idempotent job claim in a DB transaction)
- Pipeline: `processing/src/payscope_processing/pipeline.py`

Flow:
1. Load artifact metadata (format, object_key) and latest `report_id` from `report_uploads`
2. Phase 2 extraction runs (PDF/CSV/XLSX parsing + layout tagging)
3. Phase 3 normalization runs:
   - Tabular: LLM mapping → canonical rows → validation → dedupe
   - PDF: LayoutLMv3 element predictions → row assembly + validation + dedupe, plus LLM lifecycle inference
4. Persist canonical result JSON:
   - `normalized/<artifact_id>/transactions.json`

### Outputs

Normalized result (`NormalizationResult`) includes:
- `report_fact`
- `transactions[]`
- `mapping` (LLM decisions + rationales) where available
- `errors[]` structured validation/mapping errors




