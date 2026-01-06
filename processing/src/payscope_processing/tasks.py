from __future__ import annotations

import asyncpg
import logging
import os
from celery import shared_task

from payscope_processing.config import get_settings
from payscope_processing.logging import configure_logging
from payscope_processing.pipeline import run_pipeline
from payscope_processing.reliability.retry import backoff_with_jitter
from payscope_processing.reliability.dlq import write_dlq
from payscope_processing.persistence.postgres_timescale import persist_report_and_transactions, persist_timeseries
from payscope_processing.persistence.neo4j_persist import persist_graph
from payscope_processing.persistence.pinecone_persist import persist_embeddings
from payscope_processing.persistence.logs import log_stage
from payscope_processing.vector.embedder import Embedder, EmbeddingConfig
from payscope_processing.vector.pinecone_client import PineconeConfig
from payscope_processing.graph.neo4j_writer import Neo4jConfig


def _boot_logging() -> None:
    settings = get_settings()
    configure_logging(service_name=os.getenv("SERVICE_NAME", settings.service_name), level=settings.log_level)


@shared_task(
    name="payscope_processing.tasks.parse_artifact",
    bind=True,
    max_retries=5,
)
def parse_artifact(self, artifact_id: str, bank_id: str) -> str:
    """
    Idempotent parsing entrypoint.

    Guarantees:
      - A given artifact_id is processed at most once to SUCCESS.
      - Safe retries: if STARTED/SUCCESS, task returns without re-processing.
    """
    _boot_logging()
    log = logging.getLogger(__name__)
    settings = get_settings()

    async def run() -> str:
        pool = await asyncpg.create_pool(settings.database_dsn, min_size=1, max_size=5)
        try:
            async with pool.acquire() as conn:
                # Claim the job idempotently in a single DB transaction.
                async with conn.transaction():
                    row = await conn.fetchrow(
                        """
                        SELECT pj.job_id, pj.status, a.file_format, a.pdf_kind, a.object_key
                        FROM parse_jobs pj
                        JOIN artifacts a ON a.artifact_id = pj.artifact_id
                        WHERE pj.artifact_id = $1::uuid
                        FOR UPDATE
                        """,
                        artifact_id,
                    )
                    if row is None:
                        raise RuntimeError(f"parse job not found for artifact_id={artifact_id}")

                    status = row["status"]
                    if status == "SUCCESS":
                        log.info("parse_idempotent_skip_success")
                        return "already_success"
                    if status == "STARTED":
                        log.info("parse_idempotent_skip_started")
                        return "already_started"

                    await conn.execute(
                        """
                        UPDATE parse_jobs
                        SET status = 'STARTED', error = NULL, updated_at = now()
                        WHERE artifact_id = $1::uuid
                        """,
                        artifact_id,
                    )

                file_format = row["file_format"]
                pdf_kind = row["pdf_kind"]
                object_key = row["object_key"]

                # Use most recent report_id for this artifact for canonical ReportFact.report_id
                upload = await conn.fetchrow(
                    """
                    SELECT report_id::text AS report_id, upload_time AT TIME ZONE 'UTC' AS upload_time_utc
                    FROM report_uploads
                    WHERE artifact_id = $1::uuid
                    ORDER BY upload_time DESC
                    LIMIT 1
                    """,
                    artifact_id,
                )
                report_id = upload["report_id"] if upload else artifact_id
                ingestion_time_iso = (
                    upload["upload_time_utc"].replace(tzinfo=None).isoformat() + "+00:00"
                    if upload and upload["upload_time_utc"]
                    else None
                )
                source_network = "UNKNOWN"

                log.info(f"parse_route format={file_format} pdf_kind={pdf_kind}")

                # Run Phase 2 pipeline (download -> parse -> extract -> tag)
                outputs = await run_pipeline(
                    settings=settings,
                    bank_id=bank_id,
                    artifact_id=artifact_id,
                    report_id=report_id,
                    ingestion_time_iso=ingestion_time_iso,
                    source_network=source_network,
                    file_format=str(file_format),
                    pdf_kind=str(pdf_kind) if pdf_kind is not None else None,
                    object_key=str(object_key),
                )
                log.info(f"parse_outputs {outputs}")

                norm = outputs.get("normalization_result")
                if norm is None:
                    raise RuntimeError("normalization_result missing")

            # Persist to Postgres/Timescale (atomic per report)
            await persist_report_and_transactions(pool=pool, bank_id=bank_id, norm=norm)
            await persist_timeseries(pool=pool, bank_id=bank_id, norm=norm)

            # Graph after DB commit
            if settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password:
                import anyio

                try:
                    await anyio.to_thread.run_sync(
                        persist_graph,
                        cfg=Neo4jConfig(uri=settings.neo4j_uri, user=settings.neo4j_user, password=settings.neo4j_password),
                        bank_id=bank_id,
                        norm=norm,
                    )
                except Exception:
                    log_stage("neo4j", bank_id, report_id, "failure")
                    raise

            # Pinecone embeddings
            if settings.pinecone_api_key and settings.pinecone_index_name:
                import anyio

                embedder = Embedder(EmbeddingConfig(model_name=settings.embedding_model_name, device=settings.embedding_device))
                try:
                    await anyio.to_thread.run_sync(
                        persist_embeddings,
                        embedder=embedder,
                        pine_cfg=PineconeConfig(
                            api_key=settings.pinecone_api_key,
                            index_name=settings.pinecone_index_name,
                            namespace=settings.pinecone_namespace,
                        ),
                        bank_id=bank_id,
                        norm=norm,
                    )
                except Exception:
                    log_stage("pinecone", bank_id, report_id, "failure")
                    raise

            # Mark success
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE parse_jobs
                    SET status = 'SUCCESS', error = NULL, updated_at = now()
                    WHERE artifact_id = $1::uuid
                    """,
                    artifact_id,
                )
            log_stage("postgres", bank_id, report_id, "success")
            return "success"
        except Exception as e:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE parse_jobs
                    SET status = 'FAILED', error = $2, updated_at = now()
                    WHERE artifact_id = $1::uuid
                    """,
                    artifact_id,
                    str(e),
                )
            log_stage("postgres", bank_id, report_id if 'report_id' in locals() else artifact_id, "failure")
            raise
        finally:
            await pool.close()

    import anyio

    try:
        return anyio.run(run)
    except Exception as exc:
        # Reliability: exponential backoff with jitter, capped; DLQ after max retries.
        attempt = int(getattr(self.request, "retries", 0))
        if attempt >= int(self.max_retries or 0):
            # DLQ persist
            settings = get_settings()
            async def dlq_write():
                conn = await asyncpg.connect(settings.database_dsn)
                try:
                    await write_dlq(
                        conn=conn,
                        task_name=self.name,
                        task_id=str(self.request.id),
                        artifact_id=artifact_id,
                        error=str(exc),
                        payload={"artifact_id": artifact_id},
                    )
                finally:
                    await conn.close()
            import anyio as _anyio
            _anyio.run(dlq_write)
            raise
        countdown = backoff_with_jitter(attempt, base_s=2, cap_s=300)
        raise self.retry(exc=exc, countdown=countdown)


