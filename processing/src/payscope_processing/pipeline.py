from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict
from typing import Any

import anyio
from datetime import datetime, timezone

from payscope_processing.config import Settings
from payscope_processing.contracts import IntermediateDocument, LayoutUnderstandingOutput
from payscope_processing.layout.layoutlmv3_tagger import LayoutLMv3Tagger
from payscope_processing.pdf.language import detect_language
from payscope_processing.pdf.ocr_pdf import parse_scanned_pdf_via_ocr
from payscope_processing.pdf.unstructured_pdf import parse_digital_pdf
from payscope_processing.storage import build_s3_client, download_to_file, upload_json_bytes
from payscope_processing.tabular.csv_excel import parse_csv, parse_xlsx
from payscope_processing.normalize.flow import normalize_pdf_elements, normalize_tabular


async def run_pipeline(
    *,
    settings: Settings,
    artifact_id: str,
    bank_id: str,
    report_id: str,
    ingestion_time_iso: str | None,
    source_network: str,
    file_format: str,
    pdf_kind: str | None,
    object_key: str,
) -> dict[str, Any]:
    """
    Phase 2 pipeline:
      1) Download raw object
      2) Parse into normalized intermediate JSON
      3) Run layout understanding (LayoutLMv3) where applicable
      4) Persist JSON outputs back to object storage (schema-agnostic)
    """
    log = logging.getLogger(__name__)
    s3 = build_s3_client(settings)
    ingestion_time = (
        datetime.fromisoformat(ingestion_time_iso) if ingestion_time_iso else datetime.now(timezone.utc)
    )

    with tempfile.TemporaryDirectory() as td:
        raw_path = os.path.join(td, "raw")
        await anyio.to_thread.run_sync(
            download_to_file,
            s3_client=s3,
            bucket=settings.s3_bucket,
            key=object_key,
            file_path=raw_path,
        )

        outputs: dict[str, Any] = {"artifact_id": artifact_id, "raw_object_key": object_key}

        # 2.1 / 2.2 Parse
        normalization_result = None

        if file_format == "PDF":
            if pdf_kind == "SCANNED":
                intermediate = parse_scanned_pdf_via_ocr(
                    artifact_id=artifact_id, object_key=object_key, file_path=raw_path
                )
            else:
                intermediate = parse_digital_pdf(
                    artifact_id=artifact_id, object_key=object_key, file_path=raw_path
                )

            # language detection (post-parse)
            sample_text = "\n".join([e.text for e in intermediate.elements[:200]])
            outputs["detected_language"] = detect_language(sample_text)

            inter_key = f"extracted/{artifact_id}/intermediate.json"
            inter_bytes = intermediate.model_dump_json(indent=None).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=inter_key,
                data=inter_bytes,
            )
            outputs["intermediate_object_key"] = inter_key

            # 2.3 Layout understanding / field tagging
            tagger = LayoutLMv3Tagger()
            layout_out = tagger.tag(intermediate)
            layout_key = f"extracted/{artifact_id}/layout.json"
            layout_bytes = layout_out.model_dump_json(indent=None).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=layout_key,
                data=layout_bytes,
            )
            outputs["layout_object_key"] = layout_key

            # Phase 3: semantic normalization (PDF)
            norm = normalize_pdf_elements(
                settings=settings,
                bank_id=bank_id,
                artifact_id=artifact_id,
                report_id=report_id,
                report_type="pdf_report",
                ingestion_time=ingestion_time,
                source_network=source_network,
                source_object_key=object_key,
                intermediate=intermediate,
                layout=layout_out,
            )
            normalization_result = norm
            norm_key = f"normalized/{artifact_id}/transactions.json"
            norm_bytes = norm.model_dump_json(indent=None).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=norm_key,
                data=norm_bytes,
            )
            outputs["normalized_object_key"] = norm_key

        elif file_format == "CSV":
            tab = parse_csv(artifact_id=artifact_id, object_key=object_key, file_path=raw_path)
            tab_key = f"extracted/{artifact_id}/tabular.json"
            tab_bytes = json.dumps(asdict(tab), ensure_ascii=False).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=tab_key,
                data=tab_bytes,
            )
            outputs["tabular_object_key"] = tab_key

            # Phase 3: semantic normalization (tabular)
            norm = normalize_tabular(
                settings=settings,
                bank_id=bank_id,
                artifact_id=artifact_id,
                report_id=report_id,
                report_type="csv_report",
                ingestion_time=ingestion_time,
                source_network=source_network,
                source_object_key=object_key,
                tabular_json=json.loads(tab_bytes.decode("utf-8")),
            )
            normalization_result = norm
            norm_key = f"normalized/{artifact_id}/transactions.json"
            norm_bytes = norm.model_dump_json(indent=None).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=norm_key,
                data=norm_bytes,
            )
            outputs["normalized_object_key"] = norm_key
        elif file_format == "XLSX":
            tab = parse_xlsx(artifact_id=artifact_id, object_key=object_key, file_path=raw_path)
            tab_key = f"extracted/{artifact_id}/tabular.json"
            tab_bytes = json.dumps(asdict(tab), ensure_ascii=False).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=tab_key,
                data=tab_bytes,
            )
            outputs["tabular_object_key"] = tab_key

            # Phase 3: semantic normalization (tabular)
            norm = normalize_tabular(
                settings=settings,
                bank_id=bank_id,
                artifact_id=artifact_id,
                report_id=report_id,
                report_type="xlsx_report",
                ingestion_time=ingestion_time,
                source_network=source_network,
                source_object_key=object_key,
                tabular_json=json.loads(tab_bytes.decode("utf-8")),
            )
            normalization_result = norm
            norm_key = f"normalized/{artifact_id}/transactions.json"
            norm_bytes = norm.model_dump_json(indent=None).encode("utf-8")
            await anyio.to_thread.run_sync(
                upload_json_bytes,
                s3_client=s3,
                bucket=settings.s3_bucket,
                key=norm_key,
                data=norm_bytes,
            )
            outputs["normalized_object_key"] = norm_key
        else:
            raise RuntimeError(f"unsupported file_format={file_format}")

        log.info("phase2_pipeline_complete")
        outputs["normalization_result"] = normalization_result
        return outputs


