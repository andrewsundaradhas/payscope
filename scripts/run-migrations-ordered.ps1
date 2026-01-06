# Run database migrations in correct order

param(
    [string]$DatabaseUrl = $env:DATABASE_URL
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Database Migrations" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check psql
try {
    $psqlVersion = psql --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "psql not available"
    }
    Write-Host "[OK] psql is available" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] psql not found. Install PostgreSQL client tools." -ForegroundColor Red
    exit 1
}

# Set default DATABASE_URL if not provided
if (-not $DatabaseUrl) {
    $DatabaseUrl = "postgresql://payscope:payscope@localhost:5432/payscope"
    Write-Host "[INFO] Using default DATABASE_URL: $DatabaseUrl" -ForegroundColor Yellow
    Write-Host "Note: Using localhost (for psql outside Docker)" -ForegroundColor Gray
} else {
    Write-Host "[INFO] Using DATABASE_URL: $DatabaseUrl" -ForegroundColor Yellow
}

Write-Host ""

# Define migrations in order
$migrations = @(
    @{
        Name = "Canonical Facts Schema"
        Path = "infra/postgres/001_canonical_facts.sql"
        Order = 1
    },
    @{
        Name = "Explainability Audit Schema"
        Path = "infra/postgres/002_explainability_audit.sql"
        Order = 2
    },
    @{
        Name = "Row Level Security (RLS)"
        Path = "infra/postgres/003_rls_tenant.sql"
        Order = 3
    },
    @{
        Name = "TimescaleDB Metrics"
        Path = "infra/timescale/001_metrics_timeseries.sql"
        Order = 4
    }
)

# Verify all migration files exist
$missingFiles = @()
foreach ($migration in $migrations) {
    if (-not (Test-Path $migration.Path)) {
        $missingFiles += $migration.Path
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "[FAIL] Missing migration files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "[OK] All migration files found" -ForegroundColor Green
Write-Host ""

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Yellow
try {
    $testResult = psql $DatabaseUrl -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database connection successful" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Database connection failed" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
        Write-Host ""
        Write-Host "Make sure PostgreSQL is running and accessible:" -ForegroundColor Yellow
        Write-Host "  - If using Docker: docker compose up -d postgres" -ForegroundColor White
        Write-Host "  - Wait for PostgreSQL to fully start (5-10 seconds)" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "[FAIL] Database connection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Run migrations in order
$failedMigrations = @()
foreach ($migration in $migrations) {
    Write-Host "[$($migration.Order)/$($migrations.Count)] Running: $($migration.Name)..." -ForegroundColor Yellow
    Write-Host "  File: $($migration.Path)" -ForegroundColor Gray
    
    try {
        $output = psql $DatabaseUrl -f $migration.Path 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Success" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] Failed" -ForegroundColor Red
            if ($output) {
                Write-Host $output -ForegroundColor Red
            }
            $failedMigrations += $migration.Name
        }
    } catch {
        Write-Host "  [FAIL] Error: $_" -ForegroundColor Red
        $failedMigrations += $migration.Name
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($failedMigrations.Count -eq 0) {
    Write-Host "[OK] All migrations completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Verify tables created:" -ForegroundColor White
    Write-Host "   psql `$DATABASE_URL -c '\dt'" -ForegroundColor Gray
    Write-Host "2. Check RLS policies:" -ForegroundColor White
    Write-Host "   psql `$DATABASE_URL -c 'SELECT polname FROM pg_policies;'" -ForegroundColor Gray
    Write-Host "3. Verify TimescaleDB hypertables:" -ForegroundColor White
    Write-Host "   psql `$DATABASE_URL -c 'SELECT * FROM timescaledb_information.hypertables;'" -ForegroundColor Gray
} else {
    Write-Host "[FAIL] Some migrations failed:" -ForegroundColor Red
    foreach ($failed in $failedMigrations) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Review errors above and fix issues before retrying." -ForegroundColor Yellow
    exit 1
}
Write-Host "========================================" -ForegroundColor Cyan



