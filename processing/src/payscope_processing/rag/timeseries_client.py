from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import psycopg


@dataclass(frozen=True)
class TimeseriesConfig:
    dsn: str  # e.g. postgresql://user:pass@host:5432/db


class TimeseriesClient:
    def __init__(self, cfg: TimeseriesConfig):
        self._cfg = cfg

    def fetch_metrics(
        self,
        *,
        start: Optional[dt.datetime],
        end: Optional[dt.datetime],
        source_network: Optional[str] = None,
        lifecycle_stage: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        params = {}
        clauses = []
        if start:
            clauses.append("bucket_time >= %(start)s")
            params["start"] = start
        if end:
            clauses.append("bucket_time <= %(end)s")
            params["end"] = end
        if source_network:
            clauses.append("source_network = %(network)s")
            params["network"] = source_network
        if lifecycle_stage:
            clauses.append("lifecycle_stage = %(stage)s")
            params["stage"] = lifecycle_stage
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        def q(table: str, fields: str) -> List[Dict[str, Any]]:
            sql = f"SELECT {fields} FROM {table} {where} ORDER BY bucket_time ASC LIMIT 500"
            with psycopg.connect(self._cfg.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    cols = [c.name for c in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]

        return {
            "transaction_volume": q("transaction_volume", "bucket_time, source_network, lifecycle_stage, tx_count, amount_sum"),
            "fraud_counts": q("fraud_counts", "bucket_time, source_network, lifecycle_stage, fraud_count"),
            "dispute_rates": q("dispute_rates", "bucket_time, source_network, lifecycle_stage, dispute_count, tx_count, dispute_rate"),
        }




