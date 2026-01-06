"""
Admin validation endpoints for dataset verification.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import Depends, HTTPException
from neo4j import GraphDatabase
from pinecone import Pinecone

from payscope_api.security.auth import get_request_context
from payscope_api.security.context import RequestContext
from payscope_api.security.rbac import AccessDenied, POLICY_ADMIN

logger = logging.getLogger(__name__)


def _log(component: str, event: str, severity: str, tenant_id: str) -> None:
    logger.info(
        json.dumps(
            {
                "component": component,
                "event": event,
                "severity": severity,
                "tenant_id": tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
    )


async def validate_datasets(ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    """
    Admin endpoint to validate datasets per bank_id.

    Returns row counts for Postgres, Neo4j, and Pinecone per bank.
    """
    try:
        POLICY_ADMIN.check(ctx)
    except AccessDenied:
        _log("security", "access_denied", "WARN", ctx.bank_id)
        raise HTTPException(status_code=403, detail="access_denied")

    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_DSN")
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "banks": {},
    }

    # Query Postgres/TimescaleDB
    try:
        conn = await asyncpg.connect(database_url)
        try:
            # Get all banks (from reports table)
            bank_ids = await conn.fetch("SELECT DISTINCT bank_id FROM reports")
            banks = [str(row["bank_id"]) for row in bank_ids]

            for bank_id in banks:
                # Set RLS context
                await conn.execute("SET app.current_bank_id = $1", bank_id)

                # Count reports
                report_count = await conn.fetchval("SELECT COUNT(*) FROM reports")
                # Count transactions
                tx_count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
                # Count time-series buckets
                ts_count = await conn.fetchval("SELECT COUNT(*) FROM transaction_volume")

                results["banks"][bank_id] = {
                    "postgres": {
                        "reports": report_count,
                        "transactions": tx_count,
                        "timeseries_buckets": ts_count,
                    },
                    "neo4j": {},
                    "pinecone": {},
                }

        finally:
            await conn.close()
    except Exception as e:
        logger.exception("Postgres validation failed")
        results["error"] = f"Postgres query failed: {str(e)}"

    # Query Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if neo4j_password:
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            try:
                with driver.session() as session:
                    # Count nodes by type
                    node_counts = session.run(
                        """
                        MATCH (n)
                        RETURN labels(n)[0] AS node_type, COUNT(*) AS count
                        """
                    )
                    node_summary = {}
                    for record in node_counts:
                        node_summary[record["node_type"]] = record["count"]

                    # Count edges by type
                    edge_counts = session.run(
                        """
                        MATCH ()-[r]->()
                        RETURN type(r) AS edge_type, COUNT(*) AS count
                        """
                    )
                    edge_summary = {}
                    for record in edge_counts:
                        edge_summary[record["edge_type"]] = record["count"]

                    # Aggregate to all banks (Neo4j doesn't have per-bank isolation in this query)
                    # Store at top level
                    results["neo4j"] = {
                        "nodes": node_summary,
                        "edges": edge_summary,
                        "total_nodes": sum(node_summary.values()),
                        "total_edges": sum(edge_summary.values()),
                    }

            finally:
                driver.close()
        except Exception as e:
            logger.exception("Neo4j validation failed")
            results["neo4j_error"] = str(e)

    # Query Pinecone
    pinecone_key = os.getenv("PINECONE_API_KEY")
    pinecone_index = os.getenv("PINECONE_INDEX_NAME")
    pinecone_namespace = os.getenv("PINECONE_NAMESPACE", "payscope")

    if pinecone_key and pinecone_index:
        try:
            pc = Pinecone(api_key=pinecone_key)
            index = pc.Index(pinecone_index)

            # Get index stats
            stats = index.describe_index_stats()
            namespace_stats = stats.get("namespaces", {}).get(pinecone_namespace, {})

            results["pinecone"] = {
                "namespace": pinecone_namespace,
                "vector_count": namespace_stats.get("vector_count", 0),
                "index_total": stats.get("total_vector_count", 0),
            }

        except Exception as e:
            logger.exception("Pinecone validation failed")
            results["pinecone_error"] = str(e)

    _log("admin", "validate_datasets", "INFO", ctx.bank_id)
    return results

