from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from payscope_processing.graph.neo4j_writer import GraphWriter, Neo4jConfig
from payscope_processing.vector.pinecone_client import PineconeConfig, PineconeStore


@dataclass
class VectorMemory:
    store: PineconeStore

    def search(self, embedding: List[float], top_k: int = 5, filter: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self.store.query(embedding=embedding, top_k=top_k, filter=filter or {})

    def upsert(self, items: List[tuple[str, List[float], Dict[str, Any]]]) -> None:
        self.store.upsert(vectors=items)


@dataclass
class GraphContext:
    writer: GraphWriter  # used in read-only mode here

    def fetch_transaction(self, transaction_pk: str):
        # Read-only helper; does not mutate graph
        with self.writer._driver.session() as session:
            res = session.run(
                "MATCH (t:Transaction {transaction_pk: $pk}) RETURN t LIMIT 1", pk=transaction_pk
            )
            record = res.single()
            if record:
                return dict(record["t"])
            return None


@dataclass
class Scratchpad:
    """
    Ephemeral, per-agent; never persisted.
    """
    data: Dict[str, Any]


@dataclass
class DecisionLogger:
    """
    Persisted structured decision traces (could route to file/DB/log sink).
    Here we forward to the Python logger for auditable records.
    """

    logger: logging.Logger

    def log(self, payload: Dict[str, Any]) -> None:
        self.logger.info(payload)


def build_vector_memory(cfg: PineconeConfig) -> VectorMemory:
    store = PineconeStore(cfg)
    return VectorMemory(store=store)


def build_graph_context(cfg: Neo4jConfig) -> GraphContext:
    writer = GraphWriter(cfg)
    return GraphContext(writer=writer)




