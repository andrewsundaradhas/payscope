from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from payscope_processing.agents.memory import GraphContext, VectorMemory
from payscope_processing.vector.embedder import Embedder, EmbeddingConfig
from payscope_processing.vector.chunker import Chunk
from payscope_processing.rag.timeseries_client import TimeseriesClient


def infer_time_window(query: str) -> tuple[Optional[dt.datetime], Optional[dt.datetime]]:
    # Simple heuristic: default last 30 days; extend to 90 if "quarter" mentioned.
    now = dt.datetime.utcnow()
    if "quarter" in query.lower():
        return now - dt.timedelta(days=90), now
    return now - dt.timedelta(days=30), now


def retrieve_context(
    *,
    query: str,
    embedder: Embedder,
    vector_memory: VectorMemory,
    graph: GraphContext,
    timeseries: TimeseriesClient,
    filters: Dict[str, Any],
    top_k: int = 8,
) -> Dict[str, Any]:
    """
    Combined retrieval: vector + graph + time-series.
    Deterministic ordering and traceable payloads.
    """
    start, end = infer_time_window(query)

    # Vector retrieval
    embedding = embedder.embed([query])[0]
    vector_results = vector_memory.search(embedding=embedding, top_k=top_k, filter=filters.get("vector_filter"))
    vector_hits = vector_results.get("matches", []) if vector_results else []
    vector_hits = sorted(vector_hits, key=lambda x: -x.get("score", 0))[:top_k]

    # Graph retrieval (read-only)
    graph_nodes: List[Dict[str, Any]] = []
    for hit in vector_hits:
        meta = hit.get("metadata", {}) or {}
        tx_pk = meta.get("transaction_pk")
        if tx_pk:
            node = graph.fetch_transaction(tx_pk)
            if node:
                graph_nodes.append(node)

    # Timeseries retrieval
    ts = timeseries.fetch_metrics(
        start=start,
        end=end,
        source_network=filters.get("source_network"),
        lifecycle_stage=filters.get("lifecycle_stage"),
    )

    return {
        "vector_hits": vector_hits,
        "graph_nodes": graph_nodes,
        "timeseries": ts,
        "time_window": {"start": start.isoformat() if start else None, "end": end.isoformat() if end else None},
    }




