"""
Prometheus metrics endpoint for observability.
"""

from __future__ import annotations

from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.registry import CollectorRegistry

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Create a registry for custom metrics
registry = CollectorRegistry()

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Chat/Query metrics
chat_queries_total = Counter(
    "chat_queries_total",
    "Total chat queries",
    ["intent", "status"],
    registry=registry,
)

chat_query_duration_seconds = Histogram(
    "chat_query_duration_seconds",
    "Chat query duration in seconds",
    ["intent"],
    registry=registry,
)

# Agent metrics
agent_executions_total = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_name", "status"],
    registry=registry,
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name"],
    registry=registry,
)

# Database metrics
db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["operation", "status"],
    registry=registry,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    registry=registry,
)

# Vector search metrics
vector_searches_total = Counter(
    "vector_searches_total",
    "Total vector searches",
    ["status"],
    registry=registry,
)

vector_search_duration_seconds = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration in seconds",
    registry=registry,
)

# Active connections gauge
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
    ["type"],
    registry=registry,
)

# Error metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["type", "component"],
    registry=registry,
)


@router.get("")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    return generate_latest(registry)



