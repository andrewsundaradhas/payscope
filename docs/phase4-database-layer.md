## Phase 4 — Database Layer

Objective: persist normalized payment intelligence across multiple purpose-built stores (facts, metrics, semantics, relationships) with strong consistency and traceability.

### 4.1 PostgreSQL — Canonical Facts Store

**DDL**: `infra/postgres/001_canonical_facts.sql`

Tables:
- `reports`
- `transactions`
- `merchants`
- `issuers`

Design decisions (brief):
- **UUID primary keys** for all tables (`id UUID PRIMARY KEY DEFAULT gen_random_uuid()`).
- **Schema versioning**: `schema_version TEXT NOT NULL` on all tables; unique keys include schema_version where appropriate.
- **Referential integrity**: `transactions` references `reports`, `merchants`, `issuers` via FK UUIDs.
- **Idempotent inserts / dedupe**: enforced by a UNIQUE index:
  - `transactions(transaction_id, lifecycle_stage, schema_version)`
  - Upserts should use `INSERT ... ON CONFLICT (...) DO UPDATE` keyed by that constraint.

Required indexes:
- `transactions.transaction_id` → `idx_transactions_transaction_id`
- `transactions.merchant_pk` (join) → `idx_transactions_merchant_pk`
- `transactions.timestamp_utc` → `idx_transactions_timestamp`

Write pattern (canonical facts):
- Upsert `reports` by `(report_id, schema_version)`
- Upsert `merchants` by `(merchant_id, schema_version)`
- Upsert `issuers` by `(issuer_id, schema_version)`
- Upsert `transactions` by `(transaction_id, lifecycle_stage, schema_version)` and set mutable fields (amount, timestamp, confidence, report_pk, etc.)

Read patterns (examples):
- Report slice: join `transactions` → `reports` on `report_pk`
- Merchant analytics: join `transactions` → `merchants` on `merchant_pk`, filter by `timestamp_utc`

### 4.2 TimescaleDB — Metrics & Time-Series

**DDL**: `infra/timescale/001_metrics_timeseries.sql`

Hypertables (time partitioning on `bucket_time`):
- `transaction_volume`
- `fraud_counts`
- `dispute_rates`

Append-only:
- Enforced by triggers preventing UPDATE/DELETE on the time-series tables.

Aggregation & downsampling:
- Continuous aggregate: `transaction_volume_daily` (hourly→daily) with refresh policy.

Retention policies (defaults in DDL; adjust per compliance needs):
- Raw retention: 90–365 days depending on table
- Downsampled retention: 2 years for daily aggregates

Write pattern:
- Append new bucketed rows only (immutable)

Read pattern:
- Time-bucketed queries by `(bucket_time, source_network, lifecycle_stage)` with indexed access.

### 4.3 Pinecone — Vector Database

Client module:
- `processing/src/payscope_processing/vector/pinecone_client.py`

Embedded objects (per requirement):
- report sections
- transactions
- summaries

Metadata tagging (required):
- `report_id`
- `lifecycle_stage`
- `source_type` (`report_section|transaction|summary`)

Traceability / cross-store linkage (recommended metadata keys):
- `report_pk` (Postgres `reports.id`)
- `transaction_pk` (Postgres `transactions.id`)
- `merchant_pk` (Postgres `merchants.id`)
- `artifact_id` / `object_key` (raw lineage)

Write pattern:
- `upsert([(vector_id, embedding, metadata), ...])` into namespace

Read pattern:
- `query(embedding, top_k, filter={...})` for filtered semantic retrieval

### 4.4 Neo4j — Graph Database

Schema (constraints/indexes):
- `infra/neo4j/001_schema.cypher`

Node types:
- `Transaction`, `Merchant`, `Bank`, `Network`

Edge types:
- `AUTHORIZED`, `CLEARED`, `SETTLED`, `DISPUTED`

Duplicate prevention:
- Uniqueness constraints on node keys (`transaction_pk`, `merchant_pk`, `bank_pk`, `network.name`)
- Relationship de-dup via unique `edge_id`

Temporal ordering:
- Implemented in the writer logic by sorting `event_time` and rejecting out-of-order writes.

Writer module:
- `processing/src/payscope_processing/graph/neo4j_writer.py`

Write pattern:
- `MERGE` nodes by canonical UUIDs from Postgres
- `MERGE` edges by deterministic `edge_id`

Read pattern:
- Traversal from `Transaction` through stage edges for end-to-end lifecycle flow
- Merchant/network traversals for relationship analytics

### Cross-store ID linkage strategy (critical)

Authoritative IDs live in PostgreSQL (UUID PKs). All other stores must reference those IDs:
- Timescale rows include dimensions (`source_network`, `lifecycle_stage`) and optionally `report_pk` if needed for provenance.
- Pinecone metadata carries `transaction_pk`, `report_pk`, etc. for canonical traceability.
- Neo4j node properties use `transaction_pk`, `merchant_pk`, `bank_pk` to remain linkable to Postgres.




