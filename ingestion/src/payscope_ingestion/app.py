from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

import anyio
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from payscope_ingestion.celery_client import build_celery
from payscope_ingestion.config import get_settings
from payscope_ingestion.db import build_engine, build_sessionmaker
from payscope_ingestion.detect import detect_file_format
from payscope_ingestion.logging import configure_logging
from payscope_ingestion.models import Artifact, Base, JobStatus, ParseJob, ReportUpload
from payscope_ingestion.storage import build_s3_client, delete_object, put_object_file


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(service_name=settings.service_name, level=settings.log_level)
    log = logging.getLogger(__name__)

    engine = build_engine(settings)
    sm = build_sessionmaker(engine)

    s3 = build_s3_client(settings)
    celery = build_celery(settings)

    app = FastAPI(title="PayScope Ingestion", version="1.0.0")

    @app.on_event("startup")
    async def _startup() -> None:
        # Minimal production-safe baseline: ensure schema exists.
        # (If you adopt migrations later, remove create_all and run migrations in deploy.)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("startup_complete")

    @app.post("/upload")
    async def upload(
        files: list[UploadFile] = File(...),
        x_uploader: str | None = Header(default=None, alias="X-Uploader"),
        x_bank_id: str | None = Header(default=None, alias="X-Bank-Id"),
    ) -> dict[str, Any]:
        """
        Multi-file upload. Each file results in a unique report_id (UUIDv4).
        Raw content is stored in S3/MinIO and metadata is persisted in Postgres.

        Idempotency:
          - Parsing is deduplicated by checksum: a given checksum is associated to exactly one artifact + parse job.
        """
        if not x_bank_id:
            raise HTTPException(status_code=400, detail="missing_bank_id")
        bank_id = x_bank_id.strip()
        uploader = (x_uploader or "unknown").strip() or "unknown"

        results: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for uf in files:
            report_id = uuid.uuid4()
            tmp_path = None
            object_key: str | None = None
            created_new_artifact = False
            try:
                # Stream to temp file while hashing (atomic + bounded memory).
                h = hashlib.sha256()
                suffix = f"_{os.path.basename(uf.filename or 'upload')}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp_path = tmp.name
                    while True:
                        chunk = await uf.read(1024 * 1024)
                        if not chunk:
                            break
                        h.update(chunk)
                        tmp.write(chunk)

                checksum = h.hexdigest()
                with open(tmp_path, "rb") as f:
                    head = f.read(8)

                detection = detect_file_format(head=head, filename=uf.filename or "upload", file_path=tmp_path)

                # Canonical object key per checksum (dedupe raw storage too).
                ext = {
                    "PDF": "pdf",
                    "CSV": "csv",
                    "XLSX": "xlsx",
                }[detection.file_format.value]
                object_key = f"raw/{checksum}.{ext}"

                async with sm() as session:
                    # Check if artifact exists (idempotency by checksum)
                    existing = await session.execute(
                        select(Artifact).where(Artifact.checksum_sha256 == checksum)
                    )
                    artifact = existing.scalar_one_or_none()

                    if artifact is None:
                        # Upload to object storage first; if DB commit fails, delete the object.
                        await anyio.to_thread.run_sync(
                            put_object_file,
                            s3_client=s3,
                            bucket=settings.s3_bucket,
                            key=object_key,
                            file_path=tmp_path,
                            content_type=uf.content_type,
                        )
                        created_new_artifact = True

                        artifact = Artifact(
                            checksum_sha256=checksum,
                            file_format=detection.file_format,
                            pdf_kind=detection.pdf_kind,
                            object_key=object_key,
                        )
                        session.add(artifact)
                        await session.flush()  # populate artifact_id

                        job = ParseJob(
                            artifact_id=artifact.artifact_id,
                            status=JobStatus.queued,
                        )
                        session.add(job)
                    else:
                        # Ensure a parse job exists (should, via invariant); if not, create it.
                        job_res = await session.execute(
                            select(ParseJob).where(ParseJob.artifact_id == artifact.artifact_id)
                        )
                        job = job_res.scalar_one_or_none()
                        if job is None:
                            job = ParseJob(artifact_id=artifact.artifact_id, status=JobStatus.queued)
                            session.add(job)

                    upload_row = ReportUpload(
                        report_id=report_id,
                        artifact_id=artifact.artifact_id,
                        filename=uf.filename or "upload",
                        uploader=uploader,
                        checksum_sha256=checksum,
                        upload_time=datetime.now(timezone.utc),
                    )
                    session.add(upload_row)

                    try:
                        await session.commit()
                    except IntegrityError:
                        await session.rollback()
                        raise

                # Enqueue parse only if this artifact was newly created (dedupe parsing).
                if created_new_artifact:
                    async with sm() as session:
                        job_res = await session.execute(
                            select(ParseJob).where(ParseJob.artifact_id == artifact.artifact_id)
                        )
                        job = job_res.scalar_one()
                        async_result = await anyio.to_thread.run_sync(
                            celery.send_task,
                            "payscope_processing.tasks.parse_artifact",
                            args=[str(artifact.artifact_id), bank_id],
                        )
                        job.celery_task_id = async_result.id
                        await session.commit()
                else:
                    # Refresh job for accurate status reporting
                    async with sm() as session:
                        job_res = await session.execute(
                            select(ParseJob).where(ParseJob.artifact_id == artifact.artifact_id)
                        )
                        job = job_res.scalar_one()

                results.append(
                    {
                        "report_id": str(report_id),
                        "filename": uf.filename,
                        "upload_time": datetime.now(timezone.utc).isoformat(),
                        "uploader": uploader,
                        "checksum_sha256": checksum,
                        "file_format": detection.file_format.value,
                        "pdf_kind": detection.pdf_kind.value if detection.pdf_kind else None,
                        "artifact_id": str(artifact.artifact_id),
                        "parse_status": job.status.value,
                    }
                )
            except Exception as e:
                log.exception("upload_failed")
                # Best-effort cleanup
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                # If we uploaded a new object but later failed DB, delete it.
                # (Only safe to delete when object key is unique to checksum and we were creating it.)
                if created_new_artifact and object_key:
                    try:
                        await anyio.to_thread.run_sync(
                            delete_object,
                            s3_client=s3,
                            bucket=settings.s3_bucket,
                            key=object_key,
                        )
                    except Exception:
                        pass

                errors.append(
                    {
                        "report_id": str(report_id),
                        "filename": getattr(uf, "filename", None),
                        "error": str(e),
                    }
                )
            finally:
                try:
                    await uf.close()
                except Exception:
                    pass

        if results and errors:
            # Multi-status style response but with normal 200 body for simplicity.
            return {"uploads": results, "errors": errors}
        if errors and not results:
            raise HTTPException(status_code=400, detail={"errors": errors})
        return {"uploads": results}

    return app


app = create_app()


