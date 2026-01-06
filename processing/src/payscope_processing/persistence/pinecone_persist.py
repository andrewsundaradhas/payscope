from __future__ import annotations

from typing import Dict, List

from payscope_processing.normalize.schema import NormalizationResult
from payscope_processing.vector.chunker import chunk_transactions_for_vectors
from payscope_processing.vector.embedder import Embedder, EmbeddingConfig
from payscope_processing.vector.pinecone_client import PineconeConfig, PineconeStore
from payscope_processing.persistence.logs import log_stage


def persist_embeddings(
    *,
    embedder: Embedder,
    pine_cfg: PineconeConfig,
    bank_id: str,
    norm: NormalizationResult,
) -> None:
    store = PineconeStore(pine_cfg)

    chunks = chunk_transactions_for_vectors(
        transactions=[t.model_dump() for t in norm.transactions],
        report_id=str(norm.report_fact.report_id),
        lifecycle_stage=None,
    )
    if not chunks:
        log_stage("pinecone", bank_id, str(norm.report_fact.report_id), "success")
        return

    texts = [c.text for c in chunks]
    metas = []
    for c in chunks:
        meta = dict(c.source_meta)
        meta["bank_id"] = bank_id
        metas.append(meta)

    vectors = embedder.embed(texts)
    payload = []
    for i, vec in enumerate(vectors):
        meta = metas[i]
        vec_id = f"{bank_id}:{meta.get('transaction_id','tx')}-{i}"
        payload.append((vec_id, vec, meta))

    store.upsert(payload)
    log_stage("pinecone", bank_id, str(norm.report_fact.report_id), "success")




