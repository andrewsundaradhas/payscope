from __future__ import annotations

# Vector ↔ graph ↔ canonical linkage contract (metadata keys)
REQUIRED_METADATA = {
    "report_id": "UUID string matching Postgres reports.report_id",
    "lifecycle_stage": "AUTH|CLEARING|SETTLEMENT (optional for summaries)",
    "source_type": "report_section|transaction|summary",
}

RECOMMENDED_METADATA = {
    "transaction_pk": "Postgres transactions.id (UUID)",
    "report_pk": "Postgres reports.id (UUID)",
    "merchant_pk": "Postgres merchants.id (UUID)",
    "graph_node_id": "Neo4j transaction_pk or merchant_pk (mirrors Postgres UUID)",
    "artifact_id": "raw lineage",
    "object_key": "raw lineage",
}




