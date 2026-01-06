# Running Database Migrations

## Prerequisites

You need either:
1. **PostgreSQL client tools (psql)** - Recommended
2. **Docker** - Alternative method

## Migration Files (in order)

1. `infra/postgres/001_canonical_facts.sql` - Core schema
2. `infra/postgres/002_explainability_audit.sql` - Audit tables
3. `infra/postgres/003_rls_tenant.sql` - Row Level Security
4. `infra/timescale/001_metrics_timeseries.sql` - TimescaleDB hypertables

## Method 1: Using psql (Recommended)

### Install PostgreSQL Client Tools

**Windows:**
```powershell
# Using Winget
winget install PostgreSQL.PostgreSQL

# Or download from:
# https://www.postgresql.org/download/windows/
```

**After installation, verify:**
```powershell
psql --version
```

### Run Migrations

```powershell
# Set DATABASE_URL for localhost (outside Docker)
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"

# Run migrations
.\scripts\run-migrations-ordered.ps1

# Or manually:
psql $env:DATABASE_URL -f infra/postgres/001_canonical_facts.sql
psql $env:DATABASE_URL -f infra/postgres/002_explainability_audit.sql
psql $env:DATABASE_URL -f infra/postgres/003_rls_tenant.sql
psql $env:DATABASE_URL -f infra/timescale/001_metrics_timeseries.sql
```

## Method 2: Using Docker

### Prerequisites
- Docker Desktop installed and running
- PostgreSQL container running (start with `docker compose up -d postgres`)

### Run Migrations

```powershell
.\scripts\run-migrations-docker.ps1
```

### Manual Docker Method

```powershell
# Find PostgreSQL container name
docker ps | Select-String "postgres"

# Copy migration file and execute
Get-Content infra/postgres/001_canonical_facts.sql | docker exec -i postgres psql -U payscope -d payscope

# Or mount volume and execute
docker exec postgres psql -U payscope -d payscope -f /path/to/migration.sql
```

## Method 3: After Services Are Running

Once all services are started with `docker compose up -d`:

```powershell
# Copy SQL file to container
docker cp infra/postgres/001_canonical_facts.sql postgres:/tmp/

# Execute migration
docker exec postgres psql -U payscope -d payscope -f /tmp/001_canonical_facts.sql

# Repeat for each migration file
```

## Verification

After running migrations, verify:

```powershell
# List tables
psql $env:DATABASE_URL -c "\dt"

# Or with Docker:
docker exec postgres psql -U payscope -d payscope -c "\dt"

# Check RLS policies
psql $env:DATABASE_URL -c "SELECT polname FROM pg_policies;"

# Check TimescaleDB hypertables
psql $env:DATABASE_URL -c "SELECT * FROM timescaledb_information.hypertables;"
```

## Troubleshooting

### "psql: command not found"
- Install PostgreSQL client tools (see Method 1 above)

### "Connection refused"
- Start PostgreSQL: `docker compose up -d postgres`
- Wait 10-15 seconds for PostgreSQL to fully start
- Check container logs: `docker compose logs postgres`

### "Database does not exist"
- PostgreSQL should create the database automatically via docker-compose
- Or create manually: `docker exec postgres createdb -U payscope payscope`

### "Permission denied"
- Verify credentials in docker-compose.yml match .env
- Default: `payscope:payscope`

## Next Steps

After migrations complete:
1. ✅ Verify all tables created
2. ✅ Check RLS policies are active
3. ✅ Verify TimescaleDB hypertables
4. ✅ Start remaining services: `docker compose up -d`



