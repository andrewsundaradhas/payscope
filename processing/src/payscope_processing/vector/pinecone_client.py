from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from pinecone import Pinecone


@dataclass(frozen=True)
class PineconeConfig:
    api_key: str
    index_name: str
    namespace: str = "payscope"


class PineconeStore:
    """
    Vector store wrapper with traceable metadata.

    Metadata required by phase:
      - report_id (uuid string)
      - lifecycle_stage (AUTH|CLEARING|SETTLEMENT)
      - source_type (report_section|transaction|summary)

    Cross-store linkage strategy:
      - store canonical Postgres UUIDs as metadata: transaction_pk/report_pk/merchant_pk where available
    """

    def __init__(self, cfg: PineconeConfig):
        self._pc = Pinecone(api_key=cfg.api_key)
        self._index = self._pc.Index(cfg.index_name)
        self._namespace = cfg.namespace

    def upsert(
        self,
        *,
        vectors: Iterable[tuple[str, list[float], dict[str, Any]]],
    ) -> None:
        # vectors: (id, embedding, metadata)
        self._index.upsert(vectors=list(vectors), namespace=self._namespace)

    def query(
        self,
        *,
        embedding: list[float],
        top_k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter or {},
            namespace=self._namespace,
        )




