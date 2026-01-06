# Run database migrations using Docker (when psql is not available)

param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Database Migrations (Docker)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not available"
    }
    Write-Host "[OK] Docker is available" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Docker is not installed or not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternatives:" -ForegroundColor Yellow
    Write-Host "1. Install PostgreSQL client tools:" -ForegroundColor White
    Write-Host "   Download: https://www.postgresql.org/download/windows/" -ForegroundColor Gray
    Write-Host "   Or: winget install PostgreSQL.PostgreSQL" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Install Docker Desktop:" -ForegroundColor White
    Write-Host "   https://www.docker.com/products/docker-desktop/" -ForegroundColor Gray
    exit 1
}

# Check if PostgreSQL container is running
try {
    $postgresStatus = docker ps --filter "name=postgres" --format "{{.Names}}" 2>&1
    if ($postgresStatus -notmatch "postgres") {
        Write-Host "[WARNING] PostgreSQL container not running" -ForegroundColor Yellow
        Write-Host "Starting PostgreSQL service..." -ForegroundColor Yellow
        docker compose up -d postgres
        Write-Host "[OK] Waiting 10 seconds for PostgreSQL to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    } else {
        Write-Host "[OK] PostgreSQL container is running" -ForegroundColor Green
    }
} catch {
    Write-Host "[FAIL] Cannot check/start PostgreSQL: $_" -ForegroundColor Red
    exit 1
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

# Test database connection using Docker
Write-Host "Testing database connection..." -ForegroundColor Yellow
try {
    $testResult = docker exec postgres psql -U payscope -d payscope -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database connection successful" -ForegroundColor Green
    } else {
        # Try alternative container name
        $containerName = (docker ps --filter "ancestor=timescale/timescaledb:pg14-latest" --format "{{.Names}}" | Select-Object -First 1)
        if ($containerName) {
            Write-Host "[OK] Found PostgreSQL container: $containerName" -ForegroundColor Green
            $testResult = docker exec $containerName psql -U payscope -d payscope -c "SELECT version();" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Database connection successful" -ForegroundColor Green
                $script:PostgresContainer = $containerName
            } else {
                Write-Host "[FAIL] Database connection failed" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "[FAIL] PostgreSQL container not found" -ForegroundColor Red
            Write-Host "Start PostgreSQL: docker compose up -d postgres" -ForegroundColor Yellow
            exit 1
        }
    }
} catch {
    Write-Host "[FAIL] Database connection failed: $_" -ForegroundColor Red
    exit 1
}

$containerName = if ($script:PostgresContainer) { $script:PostgresContainer } else { "postgres" }

Write-Host ""

# Run migrations in order
$failedMigrations = @()
foreach ($migration in $migrations) {
    Write-Host "[$($migration.Order)/$($migrations.Count)] Running: $($migration.Name)..." -ForegroundColor Yellow
    Write-Host "  File: $($migration.Path)" -ForegroundColor Gray
    
    try {
        # Copy file to container and execute, or use stdin
        $sqlContent = Get-Content $migration.Path -Raw
        $output = echo $sqlContent | docker exec -i $containerName psql -U payscope -d payscope 2>&1
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
    Write-Host "Verify tables:" -ForegroundColor Yellow
    Write-Host "  docker exec $containerName psql -U payscope -d payscope -c '\dt'" -ForegroundColor Gray
} else {
    Write-Host "[FAIL] Some migrations failed:" -ForegroundColor Red
    foreach ($failed in $failedMigrations) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
    exit 1
}
Write-Host "========================================" -ForegroundColor Cyan



