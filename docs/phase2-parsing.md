## Phase 2 — Document Parsing & Extraction

This phase converts heterogeneous PDF/CSV/XLSX financial reports into structured, machine-readable JSON with traceability.

### Architecture (pipeline)

Single deterministic pipeline executed by the **processing** Celery worker:

1. **Fetch raw file** from object storage (S3/MinIO) using `artifact.object_key`
2. **Parse** into a **normalized intermediate representation**
   - PDF (digital): Unstructured.io
   - PDF (scanned): PaddleOCR (+ language detection)
   - CSV/XLSX: Pandas ingestion with sniffing + normalization + lineage
3. **Layout understanding + field tagging** (PDF path) using LayoutLMv3 embeddings
4. **Persist outputs** back to object storage under deterministic keys:
   - `extracted/<artifact_id>/intermediate.json`
   - `extracted/<artifact_id>/layout.json` (PDF only)
   - `extracted/<artifact_id>/tabular.json` (CSV/XLSX)

Core orchestrator: `processing/src/payscope_processing/pipeline.py`.

### Key Python modules (by requirement)

#### 2.1 PDF parsing

- **Digital PDF (Unstructured.io)**:
  - `processing/src/payscope_processing/pdf/unstructured_pdf.py`
  - Uses `unstructured.partition.pdf.partition_pdf(...)` with `infer_table_structure=True`
  - Emits ordered elements and best-effort coordinates when available

- **Scanned PDF handling**:
  - `processing/src/payscope_processing/pdf/ocr_pdf.py`
  - Uses **PaddleOCR**
  - Retains bounding boxes (pixel coords) and confidence per OCR line
  - Preserves reading order by sorting boxes top-to-bottom, left-to-right

- **Language detection (post-OCR/post-parse)**:
  - `processing/src/payscope_processing/pdf/language.py`
  - Uses `lingua-language-detector` (offline, deterministic)

**Normalized intermediate JSON contract**:

- Implemented by `processing/src/payscope_processing/contracts.py`:
  - `IntermediateDocument`
  - `IntermediateElement`
  - `BoundingBox`

Every element includes:
- `page_number`
- `element_type`
- `text`
- `bounding_box` (when available)
- `confidence` (OCR confidence when available; otherwise null)
- `source_file` (`artifact_id`, `object_key`)

#### 2.2 CSV / Excel parsing

- `processing/src/payscope_processing/tabular/csv_excel.py`
  - **Pandas ingestion**
  - Auto-detects:
    - delimiter (`csv.Sniffer` + fallback)
    - encoding (`charset-normalizer`)
    - header row (heuristic scoring)
  - Normalizes headers:
    - lowercase
    - snake_case
    - deduplicated (`normalize_headers` in `tabular/headers.py`)
  - Handles malformed rows:
    - CSV uses `on_bad_lines="skip"`
  - Preserves lineage:
    - `source_row_number` for CSV
    - `sheet_name` + `source_row_number` for XLSX

Output is schema-agnostic JSON with:
- `tables[]` containing `columns_original`, `columns_normalized`, and `rows[]` with row-level provenance.

#### 2.3 Layout understanding (LayoutLMv3)

- `processing/src/payscope_processing/layout/layoutlmv3_tagger.py`
  - Loads `LayoutLMv3Model` + `LayoutLMv3Processor` (no OCR; bboxes supplied)
  - Uses **layout + text jointly** to produce embeddings
  - Identifies:
    - **column semantics** via deterministic x-position grouping + aggregated field predictions
    - **field tags** for required types:
      - `amount`, `currency`, `transaction_id`, `date`, `status`
  - Outputs confidence scores per element and per inferred column

**Model loading + inference flow**

1. Lazy-init `LayoutLMv3Tagger` (loads model + processor)
2. Precompute deterministic **anchor embeddings** for each field type
3. For each element:
   - scale bbox to LayoutLM’s 0–1000 coordinate space
   - compute element embedding
   - compute cosine similarity to anchors
   - combine with regex heuristics and OCR confidence → final field confidence

### Data contracts between stages

- **DB → Pipeline**: `artifacts` row provides:
  - `artifact_id`, `file_format`, `pdf_kind`, `object_key`
- **Pipeline outputs (object storage)**:
  - Intermediate JSON (`IntermediateDocument`) always emitted for PDFs
  - Layout JSON (`LayoutUnderstandingOutput`) emitted for PDFs
  - Tabular JSON emitted for CSV/XLSX

### Failure handling strategy

- Worker uses `SELECT ... FOR UPDATE` on the job row for idempotency.
- On failure:
  - updates `parse_jobs.status=FAILED` and persists error string
  - Celery retries safely (max 5) with `acks_late` enabled
- No schema assumptions: parsers operate without prior knowledge of report column definitions.




