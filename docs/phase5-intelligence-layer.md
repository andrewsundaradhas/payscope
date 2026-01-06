## Phase 5 — Intelligence Layer (Vector + Graph)

Objective: cross-report, cross-lifecycle reasoning by combining graph intelligence with semantic vector retrieval.

### 5.1 Graph Construction & Reasoning

Code:
- Graph writer: `processing/src/payscope_processing/graph/neo4j_writer.py`
- Anomaly detection + lifecycle linking: `processing/src/payscope_processing/graph/reasoning.py`

Lifecycle linking:
- Joins stages by `transaction_id` (canonical) and builds edges AUTH→CLEARING→SETTLEMENT.
- Supports partial lifecycles (missing stages allowed).

Anomaly detection rules:
- Missing settlement (`missing_settlement`)
- Amount mismatch (>1% relative difference) (`has_amount_mismatch`)
- Currency conflict (`currency_conflict`)
- Timestamp order violation (`timestamp_violation`)
- Lifecycle gap duration (auth→settlement, seconds) (`lifecycle_gap_duration`)

Storage of anomalies:
- Flags are written as properties on the `Transaction` node in Neo4j.

Reasoning queries enabled:
- “Show transactions authorized but never settled” → filter `missing_settlement=true`.
- “Find merchants with abnormal lifecycle gaps” → traverse `(:Transaction {lifecycle_gap_duration > threshold})-[:AT_MERCHANT]->(:Merchant)`.

Duplicate/ordering safety:
- Nodes MERGE’d by canonical UUIDs (transaction_pk/merchant_pk/bank_pk/network).
- Edges MERGE’d by deterministic `edge_id`; temporal ordering enforced in writer (rejects out-of-order).

### 5.2 Embedding Strategy

Embedding model selection:
- Default: **`BAAI/bge-base-en-v1.5`**
  - Good retrieval performance on English & financial text
  - 768 dims (balanced latency/cost)
  - Offline-capable, open-source

Chunking strategy:
- Section-aware, avoids fixed-size splitting:
  - `vector/chunker.py::chunk_report_sections` (uses logical sections/table boundaries; preserves lifecycle relevance via metadata)
  - `vector/chunker.py::chunk_transactions_for_vectors` (one chunk per transaction for vector↔graph alignment)

Embedding + storage:
- Embedder: `vector/embedder.py` (SentenceTransformer wrapper, device-aware, normalized embeddings).
- Vector store: `vector/pinecone_client.py`
- Metadata contract: `vector/link_contract.py`
  - Required: `report_id`, `lifecycle_stage`, `source_type`
  - Recommended for traceability: `transaction_pk`, `report_pk`, `merchant_pk`, `graph_node_id`, `artifact_id`, `object_key`

Retrieval & hybrid reasoning:
- Similarity search with filters (e.g., lifecycle_stage, report_id).
- Hybrid path: **vector similarity → graph traversal** (use returned `transaction_pk`/`graph_node_id` to traverse lifecycle/merchant/network relationships in Neo4j).

### End-to-end reasoning flow (conceptual)
1) Normalize and persist facts (Postgres) + lifecycle graph (Neo4j) + anomalies on nodes.
2) Chunk reports/transactions semantically; embed with `BAAI/bge-base-en-v1.5`.
3) Upsert embeddings to Pinecone with cross-store metadata (transaction_pk/report_pk/...).
4) Query flow:
   - Run semantic search with filters (e.g., lifecycle_stage=AUTH, report_id=X).
   - For top hits, use `transaction_pk`/`graph_node_id` to:
     - Traverse lifecycle edges (find missing settlement, gaps, anomalies).
     - Expand to merchant/network subgraphs for cohort-level reasoning.




