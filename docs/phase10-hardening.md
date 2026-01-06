## Phase 10 — System Hardening

### 10.1 Security hardening

#### RBAC
- Roles: `ADMIN`, `BANK_ADMIN`, `ANALYST`, `AUDITOR`, `SYSTEM`
- API enforcement: `api/src/payscope_api/security/*`
  - JWT claims required: `sub`, `role`, `bank_id`
  - Policies are explicit (no implicit permissions): `security/rbac.py`

#### Tenant isolation (bank_id)
- PostgreSQL/Timescale:
  - `bank_id` added to fact + metrics DDL:
    - `infra/postgres/001_canonical_facts.sql`
    - `infra/timescale/001_metrics_timeseries.sql`
  - DB-level RLS enforcement:
    - `infra/postgres/003_rls_tenant.sql`
    - connection must `SET app.bank_id='<uuid>'`
- Vector DB (Pinecone): enforce per-tenant namespace or metadata filter `bank_id`
- Graph DB (Neo4j): require `bank_id` on nodes and include in MATCH patterns (design requirement)

#### Encryption
- TLS everywhere + mTLS for internal services: `infra/security/tls/README.md`
- At-rest encryption posture:
  - disk encryption for DB volumes + S3/MinIO SSE and KMS rotation (documented)

### 10.2 Performance & scalability

- Async scaling:
  - Celery supports horizontal scale; run workers with autoscale and queue depth monitoring.
- Tenant-safe caching:
  - `processing/src/payscope_processing/cache/redis_cache.py` prefixes keys with `bank_id`.

### 10.3 Reliability & operability

- Retry logic:
  - exponential backoff + jitter: `processing/src/payscope_processing/reliability/retry.py`
- DLQ:
  - persistent DLQ table + writes after max retries: `processing/src/payscope_processing/reliability/dlq.py`
  - integrated into Celery task: `processing/src/payscope_processing/tasks.py`

### Monitoring & alerts

- Prometheus metrics definitions: `processing/src/payscope_processing/metrics/prometheus.py`
- Prometheus config + alert rules:
  - `infra/monitoring/prometheus.yml`
  - `infra/monitoring/alert_rules.yml`

### Stress test plan (high level)
- Ingestion: very large PDFs + high file counts
- Load: concurrent RAG queries + parallel simulations
- Capture p50/p95/p99 latencies and error rates; verify tenant isolation under load.




