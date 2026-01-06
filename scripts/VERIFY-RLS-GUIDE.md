# Verifying RLS & bank_id Configuration

## Prerequisites

You need either:
1. **psql** installed, OR
2. **Docker** with PostgreSQL container running

## Quick Verification

Run the automated verification script:

```powershell
.\scripts\verify-rls.ps1
```

## Manual Verification

### Using psql

```powershell
# Set DATABASE_URL
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"

# Run verification queries
psql $env:DATABASE_URL -f scripts/verify-rls-sql.sql

# Or run individual commands:
psql $env:DATABASE_URL -c "\d+ reports"
psql $env:DATABASE_URL -c "\d+ transactions"
psql $env:DATABASE_URL -c "SELECT polname FROM pg_policies WHERE tablename IN ('reports','transactions','transaction_volume');"
```

### Using Docker

```powershell
# Find container name
docker ps | Select-String "postgres"

# Run verification
docker exec postgres psql -U payscope -d payscope -f /path/to/verify-rls-sql.sql

# Or individual commands:
docker exec postgres psql -U payscope -d payscope -c "\d+ reports"
docker exec postgres psql -U payscope -d payscope -c "\d+ transactions"
docker exec postgres psql -U payscope -d payscope -c "SELECT polname FROM pg_policies WHERE tablename IN ('reports','transactions','transaction_volume');"
```

## What to Verify

### 1. Table Structure (bank_id columns)

**Expected:**
- `reports` table has `bank_id` column (UUID type)
- `transactions` table has `bank_id` column (UUID type)
- `transaction_volume` table has `bank_id` column (UUID type)

**Check:**
```sql
\d+ reports;
\d+ transactions;
```

Look for `bank_id` in the column list.

### 2. RLS Enabled

**Expected:**
- `relrowsecurity = true` for all tables

**Check:**
```sql
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname IN ('reports', 'transactions', 'transaction_volume');
```

### 3. RLS Policies

**Expected:**
- At least one policy per table
- Policies enforce `bank_id` isolation using `app.current_bank_id`

**Check:**
```sql
SELECT polname, tablename, polcmd
FROM pg_policies
WHERE tablename IN ('reports','transactions','transaction_volume');
```

**Expected policies:**
- `reports_bank_id_policy` (or similar)
- `transactions_bank_id_policy` (or similar)
- `transaction_volume_bank_id_policy` (or similar)

### 4. TimescaleDB Hypertable

**Expected:**
- `transaction_volume` exists as a hypertable
- Has `bank_id` column

**Check:**
```sql
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'transaction_volume';
```

## Troubleshooting

### No bank_id columns
- Run migration: `infra/postgres/001_canonical_facts.sql`
- Run migration: `infra/timescale/001_metrics_timeseries.sql`

### RLS not enabled
- Run migration: `infra/postgres/003_rls_tenant.sql`

### No policies found
- Run migration: `infra/postgres/003_rls_tenant.sql`
- Verify migration completed without errors

### Tables don't exist
- Run all migrations in order:
  1. `001_canonical_facts.sql`
  2. `002_explainability_audit.sql`
  3. `003_rls_tenant.sql`
  4. `001_metrics_timeseries.sql`

## Success Criteria

✅ All tables have `bank_id` column (UUID)  
✅ RLS is enabled on all tables  
✅ RLS policies exist and enforce `bank_id` isolation  
✅ `transaction_volume` is a TimescaleDB hypertable with `bank_id`

## Next Steps

Once verified:
1. ✅ RLS is properly configured
2. ✅ bank_id isolation is enforced
3. ✅ Ready for multi-tenant data
4. ✅ Proceed with service deployment



