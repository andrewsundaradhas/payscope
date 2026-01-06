"""
Health check endpoints with dependency verification.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])

logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    """Health status model."""
    status: str
    checks: Dict[str, Any]


@router.get("")
async def health() -> dict:
    """
    Basic health check endpoint.
    Returns {ok: true} for frontend compatibility.
    """
    return {"ok": True, "status": "ok"}


@router.get("/ready")
async def readiness() -> HealthStatus:
    """
    Readiness probe - checks if service is ready to accept traffic.
    Verifies dependencies are available.
    """
    checks = {}
    all_ok = True

    # Check Postgres
    try:
        from payscope_processing.config import get_settings
        settings = get_settings()
        if settings.database_dsn:
            import psycopg
            with psycopg.connect(settings.database_dsn, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            checks["postgres"] = "ok"
        else:
            checks["postgres"] = "not_configured"
    except Exception as e:
        logger.warning(f"Postgres health check failed: {e}")
        checks["postgres"] = f"error: {str(e)}"
        all_ok = False

    # Check Redis
    try:
        from payscope_processing.config import get_settings
        settings = get_settings()
        if settings.redis_url:
            import redis
            r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_configured"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        checks["redis"] = f"error: {str(e)}"
        all_ok = False

    # Check Neo4j (optional)
    try:
        from payscope_processing.config import get_settings
        settings = get_settings()
        if settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                connection_timeout=2,
            )
            driver.verify_connectivity()
            driver.close()
            checks["neo4j"] = "ok"
        else:
            checks["neo4j"] = "not_configured"
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")
        checks["neo4j"] = f"error: {str(e)}"
        # Neo4j is optional, don't fail readiness

    # Check Pinecone (optional)
    try:
        from payscope_processing.config import get_settings
        settings = get_settings()
        if settings.pinecone_api_key and settings.pinecone_index_name:
            import pinecone
            pc = pinecone.Pinecone(api_key=settings.pinecone_api_key)
            index = pc.Index(settings.pinecone_index_name)
            index.describe_index_stats()
            checks["pinecone"] = "ok"
        else:
            checks["pinecone"] = "not_configured"
    except Exception as e:
        logger.warning(f"Pinecone health check failed: {e}")
        checks["pinecone"] = f"error: {str(e)}"
        # Pinecone is optional, don't fail readiness

    status = "ok" if all_ok else "degraded"
    return HealthStatus(status=status, checks=checks)


@router.get("/live")
async def liveness() -> HealthStatus:
    """
    Liveness probe - checks if service is alive.
    """
    return HealthStatus(status="ok", checks={})



