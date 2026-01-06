from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class Chunk:
    text: str
    source_meta: dict


def chunk_report_sections(
    *,
    sections: Iterable[dict],
    lifecycle_stage: str | None,
    report_id: str,
) -> List[Chunk]:
    """
    Semantic chunking (section-aware, avoids fixed-size splits):
      - Expects sections already segmented by logical boundaries (headings/tables).
      - Each section is a dict with {text, kind, page_number?, table_id?}
    """
    chunks: List[Chunk] = []
    for sec in sections:
        text = (sec.get("text") or "").strip()
        if not text:
            continue
        meta = {
            "report_id": report_id,
            "lifecycle_stage": lifecycle_stage,
            "source_type": sec.get("kind", "section"),
        }
        if sec.get("page_number"):
            meta["page_number"] = sec["page_number"]
        if sec.get("table_id"):
            meta["table_id"] = sec["table_id"]
        chunks.append(Chunk(text=text, source_meta=meta))
    return chunks


def chunk_transactions_for_vectors(
    *,
    transactions: Iterable[dict],
    report_id: str,
    lifecycle_stage: str | None,
) -> List[Chunk]:
    """
    Transaction-level chunks (one per transaction) to align vector retrieval with graph nodes.
    """
    out: List[Chunk] = []
    for t in transactions:
        text = (
            f"transaction_id: {t.get('transaction_id')} "
            f"amount: {t.get('amount')} {t.get('currency')} "
            f"timestamp: {t.get('timestamp_utc')} "
            f"merchant: {t.get('merchant_id')} "
            f"card_network: {t.get('card_network')}"
        )
        meta = {
            "report_id": report_id,
            "lifecycle_stage": lifecycle_stage,
            "source_type": "transaction",
            "transaction_id": t.get("transaction_id"),
        }
        out.append(Chunk(text=text, source_meta=meta))
    return out




