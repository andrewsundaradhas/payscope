# PayScope Database Migration Script
# Runs all SQL migrations in the correct order

param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PayScope Database Migrations" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $DatabaseUrl) {
    Write-Host "✗ DATABASE_URL not set" -ForegroundColor Red
    Write-Host "  Set DATABASE_URL environment variable or pass -DatabaseUrl parameter" -ForegroundColor Yellow
    Write-Host "  Example: \$env:DATABASE_URL='postgresql://user:pass@localhost:5432/payscope'" -ForegroundColor Gray
    exit 1
}

# Check psql availability
try {
    $psqlVersion = psql --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "psql not found"
    }
} catch {
    Write-Host "✗ psql not found. Install PostgreSQL client tools." -ForegroundColor Red
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Join-Path $scriptDir ".."
$migrations = @(
    @{
        Name = "Canonical Facts Schema"
        Path = Join-Path $repoRoot "infra" "postgres" "001_canonical_facts.sql"
        Order = 1
    },
    @{
        Name = "Explainability Audit Schema"
        Path = Join-Path $repoRoot "infra" "postgres" "002_explainability_audit.sql"
        Order = 2
    },
    @{
        Name = "Row Level Security (RLS)"
        Path = Join-Path $repoRoot "infra" "postgres" "003_rls_tenant.sql"
        Order = 3
    },
    @{
        Name = "TimescaleDB Metrics"
        Path = Join-Path $repoRoot "infra" "timescale" "001_metrics_timeseries.sql"
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
    Write-Host "✗ Missing migration files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Database URL: $DatabaseUrl" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No migrations will be executed" -ForegroundColor Yellow
    Write-Host ""
}

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Yellow
try {
    $testResult = psql $DatabaseUrl -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database connection successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Database connection failed" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Database connection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Run migrations in order
$failedMigrations = @()
foreach ($migration in $migrations | Sort-Object Order) {
    Write-Host "[$($migration.Order)/$($migrations.Count)] Running: $($migration.Name)..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "  Would run: $($migration.Path)" -ForegroundColor Gray
        continue
    }
    
    try {
        $output = psql $DatabaseUrl -f $migration.Path 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Success" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Failed" -ForegroundColor Red
            Write-Host $output -ForegroundColor Red
            $failedMigrations += $migration.Name
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
        $failedMigrations += $migration.Name
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "Dry run complete. No changes made." -ForegroundColor Yellow
} elseif ($failedMigrations.Count -eq 0) {
    Write-Host "✓ All migrations completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Verify RLS is enabled: psql \$DATABASE_URL -c '\d+ reports'" -ForegroundColor White
    Write-Host "2. Check policies: psql \$DATABASE_URL -c 'SELECT polname FROM pg_policies;'" -ForegroundColor White
    Write-Host "3. Start services and upload test data" -ForegroundColor White
} else {
    Write-Host "✗ Some migrations failed:" -ForegroundColor Red
    foreach ($failed in $failedMigrations) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Review errors above and fix issues before retrying." -ForegroundColor Yellow
    exit 1
}
Write-Host "========================================" -ForegroundColor Cyan



