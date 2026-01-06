# PayScope Setup Scripts

Helper scripts for setting up and validating PayScope deployment.

## Scripts

### `check-prerequisites.ps1`
Checks if all required system tools are installed:
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL client (psql)
- Poetry (optional)

**Usage:**
```powershell
.\scripts\check-prerequisites.ps1
```

### `setup.ps1`
Interactive setup script that:
- Runs prerequisite checks
- Creates `.env` file from template
- Optionally generates JWT keypair

**Usage:**
```powershell
.\scripts\setup.ps1
```

### `run-migrations.ps1`
Runs all database migrations in the correct order:
1. `001_canonical_facts.sql` - Core schema
2. `002_explainability_audit.sql` - Audit tables
3. `003_rls_tenant.sql` - Row Level Security
4. `001_metrics_timeseries.sql` - TimescaleDB tables

**Usage:**
```powershell
# Set DATABASE_URL first
$env:DATABASE_URL = "postgresql://user:pass@localhost:5432/payscope"

# Run migrations
.\scripts\run-migrations.ps1

# Dry run (test without executing)
.\scripts\run-migrations.ps1 -DryRun
```

### `validate-setup.ps1`
Validates that all services are running and configured correctly:
- Docker services (postgres, redis, minio, neo4j)
- API endpoints
- Database connection and migrations
- Configuration files

**Usage:**
```powershell
.\scripts\validate-setup.ps1
```

## Quick Start

1. **Check prerequisites:**
   ```powershell
   .\scripts\check-prerequisites.ps1
   ```

2. **Run setup:**
   ```powershell
   .\scripts\setup.ps1
   ```

3. **Configure .env:**
   Edit `.env` file and set:
   - Database credentials
   - JWT keys (or generate via setup script)
   - Service URLs and API keys

4. **Start services:**
   ```powershell
   docker compose up -d
   ```

5. **Run migrations:**
   ```powershell
   $env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"
   .\scripts\run-migrations.ps1
   ```

6. **Validate setup:**
   ```powershell
   .\scripts\validate-setup.ps1
   ```

## Environment Variables

Key environment variables required:

- `DATABASE_URL` - PostgreSQL connection string
- `JWT_PRIVATE_KEY` - RSA private key (PEM format)
- `JWT_PUBLIC_KEY` - RSA public key (PEM format)
- `REDIS_URL` - Redis connection string
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET` - Object storage
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` - Neo4j connection
- `PINECONE_API_KEY`, `PINECONE_INDEX` - Pinecone vector DB

See `env/local.env.example` for a complete template.



