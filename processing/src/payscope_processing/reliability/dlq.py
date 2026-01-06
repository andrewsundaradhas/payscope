from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

import asyncpg


@dataclass(frozen=True)
class DlqEvent:
    task_name: str
    task_id: str
    artifact_id: str
    error: str
    payload: Dict[str, Any]
    created_at: str


async def ensure_dlq_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dlq_events (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          task_name text NOT NULL,
          task_id text NOT NULL,
          artifact_id uuid NULL,
          error text NOT NULL,
          payload jsonb NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


async def write_dlq(
    *,
    conn: asyncpg.Connection,
    task_name: str,
    task_id: str,
    artifact_id: str | None,
    error: str,
    payload: Dict[str, Any],
) -> None:
    await ensure_dlq_table(conn)
    await conn.execute(
        """
        INSERT INTO dlq_events (task_name, task_id, artifact_id, error, payload)
        VALUES ($1, $2, $3::uuid, $4, $5::jsonb)
        """,
        task_name,
        task_id,
        artifact_id,
        error,
        json.dumps(payload, ensure_ascii=False),
    )




