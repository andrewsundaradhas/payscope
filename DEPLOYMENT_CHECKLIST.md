# PayScope Deployment Checklist

## Pre-Deployment

### 1. Environment Variables
```bash
# Verify all required environment variables are set
# Key variables:
- DATABASE_DSN (Postgres connection string)
- REDIS_URL (Redis connection string)
- JWT_PUBLIC_KEY (JWT verification key)
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (Neo4j connection)
- PINECONE_API_KEY, PINECONE_INDEX_NAME (Pinecone connection)
- LLM_BASE_URL, LLM_API_KEY (LLM connection)
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY (S3/MinIO)
```

### 2. Database Migrations
```bash
# Run Postgres migrations in order:
psql $DATABASE_DSN -f infra/postgres/001_canonical_facts.sql
psql $DATABASE_DSN -f infra/postgres/002_explainability_audit.sql  # if exists
psql $DATABASE_DSN -f infra/postgres/003_rls_tenant.sql

# Run TimescaleDB migrations:
psql $DATABASE_DSN -f infra/timescale/001_metrics_timeseries.sql
```

### 3. Neo4j Schema
```bash
# Apply Neo4j constraints and indexes:
cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD -a $NEO4J_URI -f infra/neo4j/001_schema.cypher
```

### 4. Pinecone Index
```bash
# Verify Pinecone index exists and has correct configuration
# (Should be created manually via Pinecone console or API)
```

### 5. MinIO/S3 Buckets
```bash
# Create required buckets:
# - payscope-artifacts (for raw/processed files)
# - payscope-models (for ML models)
# - payscope-backups (for backups)
```

## Deployment

### 1. Start Infrastructure Services
```bash
# Start core services (Postgres, Redis, MinIO, Neo4j):
docker compose up -d postgres redis minio neo4j

# Wait for services to be ready (check /health/ready or use wait-for scripts)
# Verify connectivity:
docker compose exec api curl http://localhost:8000/health/ready
```

### 2. Start Application Services
```bash
# Start API service:
docker compose up -d api

# Start Celery worker:
docker compose up -d worker

# Start ingestion service (if separate):
docker compose up -d ingestion
```

### 3. Verify Services
```bash
# Check API health:
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live

# Check metrics:
curl http://localhost:8000/metrics

# Verify services are running:
docker compose ps
```

## Post-Deployment Verification

### 1. Health Checks
```bash
# API service:
curl http://localhost:8000/health/ready
# Expected: {"status": "ok", "checks": {"postgres": "ok", "redis": "ok", ...}}

# All checks should be "ok" or "not_configured" (optional services)
```

### 2. Dependency Verification
```bash
# Verify Postgres connection:
docker compose exec api python -c "from payscope_processing.config import get_settings; import psycopg; conn = psycopg.connect(get_settings().database_dsn); print('OK')"

# Verify Redis connection:
docker compose exec api python -c "from payscope_processing.config import get_settings; import redis; r = redis.from_url(get_settings().redis_url); r.ping(); print('OK')"

# Verify Neo4j (if configured):
docker compose exec api python -c "from payscope_processing.config import get_settings; from neo4j import GraphDatabase; driver = GraphDatabase.driver(get_settings().neo4j_uri, auth=(get_settings().neo4j_user, get_settings().neo4j_password)); driver.verify_connectivity(); print('OK')"

# Verify Pinecone (if configured):
docker compose exec api python -c "from payscope_processing.config import get_settings; import pinecone; pc = pinecone.Pinecone(api_key=get_settings().pinecone_api_key); index = pc.Index(get_settings().pinecone_index_name); index.describe_index_stats(); print('OK')"
```

### 3. Endpoint Verification
```bash
# Test chat endpoint (requires valid JWT):
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "X-Bank-Id: <bank_uuid>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the transaction volume?", "time_range": "30d"}'

# Expected: JSON response with summary, metrics, confidence, intent, agents_invoked
```

### 4. Metrics Verification
```bash
# Check Prometheus metrics:
curl http://localhost:8000/metrics

# Expected: Prometheus-formatted metrics (text/plain)
# Key metrics:
# - http_requests_total
# - chat_queries_total
# - agent_executions_total
# - errors_total
```

### 5. Log Verification
```bash
# Check API logs:
docker compose logs api | tail -100

# Check worker logs:
docker compose logs worker | tail -100

# Verify structured logging (JSON format)
# Verify query logging (intent, agents_invoked, bank_id)
# Verify no uncaught exceptions
```

### 6. Bank Isolation Verification
```bash
# Test with different bank_ids:
# Should get 403 if JWT bank_id != X-Bank-Id header

# Test data isolation:
# Upload data for bank A, query for bank B (should return empty)
```

## Monitoring

### 1. Metrics Dashboard
```bash
# Configure Prometheus to scrape:
# - http://api:8000/metrics

# Key metrics to monitor:
# - http_requests_total (rate, error rate)
# - chat_query_duration_seconds (p95, p99)
# - agent_execution_duration_seconds (p95, p99)
# - errors_total (error rate by type)
# - db_query_duration_seconds (slow queries)
```

### 2. Health Check Monitoring
```bash
# Configure health check alerts:
# - /health/ready returns status != "ok"
# - /health/live returns status != "ok"
# - Any dependency check fails (postgres, redis, etc.)
```

### 3. Log Monitoring
```bash
# Monitor logs for:
# - Uncaught exceptions
# - High error rates
# - Slow queries (db_query_duration_seconds > threshold)
# - Bank isolation violations (403 errors)
```

## Troubleshooting

### Health Check Failures
```bash
# If /health/ready fails:
# 1. Check dependency connectivity (Postgres, Redis, Neo4j, Pinecone)
# 2. Check environment variables
# 3. Check service logs
# 4. Verify network connectivity (docker network)

# Example: Postgres check fails
# - Verify DATABASE_DSN is correct
# - Verify Postgres is running: docker compose ps postgres
# - Verify network connectivity: docker compose exec api ping postgres
```

### Metrics Not Appearing
```bash
# If /metrics returns empty:
# 1. Verify metrics router is included in app.py
# 2. Verify prometheus_client is installed
# 3. Check logs for import errors
```

### Service Not Starting
```bash
# Check logs:
docker compose logs <service>

# Common issues:
# - Missing environment variables
# - Database migrations not run
# - Port conflicts
# - Dependency services not ready
```

## Success Criteria

- ✅ All services start without errors
- ✅ /health/ready returns status "ok" with all dependencies checked
- ✅ /metrics endpoint returns Prometheus-formatted metrics
- ✅ Chat endpoint responds with structured JSON
- ✅ No uncaught exceptions in logs
- ✅ Bank isolation enforced (403 on mismatch)
- ✅ Metrics increase with requests

## Rollback Plan

If deployment fails:
1. Stop new services: `docker compose stop api worker ingestion`
2. Check logs: `docker compose logs api worker`
3. Verify environment variables
4. Rollback database migrations if needed
5. Restart services: `docker compose start <service>`



