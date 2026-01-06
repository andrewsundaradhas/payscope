from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import asyncpg

from payscope_processing.normalize.schema import NormalizationResult, TransactionFact
from payscope_processing.persistence.logs import log_stage


async def _set_tenant(conn: asyncpg.Connection, bank_id: str) -> None:
    await conn.execute("SET app.current_bank_id = $1", bank_id)


async def persist_report_and_transactions(
    *, pool: asyncpg.Pool, bank_id: str, norm: NormalizationResult
) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _set_tenant(conn, bank_id)

            rf = norm.report_fact
            report_pk = await conn.fetchval(
                """
                INSERT INTO reports (bank_id, report_id, report_type, ingestion_time, source_network, record_count, schema_version)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                ON CONFLICT (bank_id, report_id, schema_version)
                DO UPDATE SET report_type=EXCLUDED.report_type, ingestion_time=EXCLUDED.ingestion_time, source_network=EXCLUDED.source_network, record_count=EXCLUDED.record_count
                RETURNING id
                """,
                bank_id,
                rf.report_id,
                rf.report_type,
                rf.ingestion_time,
                rf.source_network,
                rf.record_count,
                rf.schema_version,
            )

            for tx in norm.transactions:
                merchant_pk = await conn.fetchval(
                    """
                    INSERT INTO merchants (bank_id, merchant_id, name, country, schema_version)
                    VALUES ($1,$2,$3,$4,$5)
                    ON CONFLICT (bank_id, merchant_id, schema_version)
                    DO UPDATE SET name=COALESCE(EXCLUDED.name, merchants.name), country=COALESCE(EXCLUDED.country, merchants.country)
                    RETURNING id
                    """,
                    bank_id,
                    tx.merchant_id,
                    None,
                    None,
                    rf.schema_version,
                )
                issuer_pk = None
                tx_pk = await conn.fetchval(
                    """
                    INSERT INTO transactions (
                      bank_id, transaction_id, lifecycle_stage, amount, currency, timestamp_utc,
                      card_network, merchant_pk, issuer_pk, report_pk, raw_source_object_key, raw_source_artifact_id,
                      confidence_score, schema_version
                    )
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                    ON CONFLICT (bank_id, transaction_id, lifecycle_stage, schema_version)
                    DO UPDATE SET amount=EXCLUDED.amount, currency=EXCLUDED.currency, timestamp_utc=EXCLUDED.timestamp_utc,
                      card_network=EXCLUDED.card_network, merchant_pk=EXCLUDED.merchant_pk, issuer_pk=EXCLUDED.issuer_pk,
                      report_pk=EXCLUDED.report_pk, raw_source_object_key=EXCLUDED.raw_source_object_key, raw_source_artifact_id=EXCLUDED.raw_source_artifact_id,
                      confidence_score=EXCLUDED.confidence_score
                    RETURNING id
                    """,
                    bank_id,
                    tx.transaction_id,
                    tx.lifecycle_stage.value,
                    tx.amount,
                    tx.currency,
                    tx.timestamp_utc,
                    tx.card_network,
                    merchant_pk,
                    issuer_pk,
                    report_pk,
                    tx.raw_source_ref.object_key,
                    tx.raw_source_ref.artifact_id,
                    tx.confidence_score,
                    rf.schema_version,
                )
            log_stage("postgres", bank_id, str(rf.report_id), "success")


async def persist_timeseries(
    *, pool: asyncpg.Pool, bank_id: str, norm: NormalizationResult
) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _set_tenant(conn, bank_id)
            rf = norm.report_fact
            # Aggregate by day
            buckets: Dict[tuple[dt.date, str, str], Dict[str, Any]] = {}
            for tx in norm.transactions:
                day = tx.timestamp_utc.date()
                key = (day, rf.source_network, tx.lifecycle_stage.value)
                b = buckets.setdefault(key, {"tx_count": 0, "amount_sum": 0})
                b["tx_count"] += 1
                b["amount_sum"] += float(tx.amount)

            for (day, net, stage), vals in buckets.items():
                bucket_time = dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)
                await conn.execute(
                    """
                    INSERT INTO transaction_volume (id, bank_id, bucket_time, source_network, lifecycle_stage, tx_count, amount_sum)
                    VALUES (gen_random_uuid(), $1,$2,$3,$4,$5,$6)
                    ON CONFLICT DO NOTHING
                    """,
                    bank_id,
                    bucket_time,
                    net,
                    stage,
                    vals["tx_count"],
                    vals["amount_sum"],
                )
            log_stage("postgres", bank_id, str(rf.report_id), "success")




