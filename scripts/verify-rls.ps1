# Verify Row Level Security (RLS) and bank_id columns

param(
    [string]$DatabaseUrl = $env:DATABASE_URL
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying RLS & bank_id Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Try psql first, fallback to Docker
$useDocker = $false
$containerName = $null

try {
    $psqlVersion = psql --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Using psql for verification" -ForegroundColor Green
    } else {
        throw "psql not available"
    }
} catch {
    Write-Host "[INFO] psql not found, trying Docker..." -ForegroundColor Yellow
    
    # Try Docker
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Find PostgreSQL container
            $containerName = docker ps --filter "ancestor=timescale/timescaledb:pg14-latest" --format "{{.Names}}" | Select-Object -First 1
            if (-not $containerName) {
                $containerName = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-Object -First 1
            }
            
            if ($containerName) {
                Write-Host "[OK] Using Docker container: $containerName" -ForegroundColor Green
                $useDocker = $true
            } else {
                Write-Host "[FAIL] PostgreSQL container not found" -ForegroundColor Red
                Write-Host "Start PostgreSQL: docker compose up -d postgres" -ForegroundColor Yellow
                exit 1
            }
        } else {
            throw "Docker not available"
        }
    } catch {
        Write-Host "[FAIL] Neither psql nor Docker available" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install one of:" -ForegroundColor Yellow
        Write-Host "  1. PostgreSQL client: winget install PostgreSQL.PostgreSQL" -ForegroundColor White
        Write-Host "  2. Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
        exit 1
    }
}

Write-Host ""

# Function to execute SQL
function Invoke-Sql {
    param([string]$Query)
    
    if ($useDocker) {
        $result = echo $Query | docker exec -i $containerName psql -U payscope -d payscope 2>&1
        return $result
    } else {
        if (-not $DatabaseUrl) {
            $DatabaseUrl = "postgresql://payscope:payscope@localhost:5432/payscope"
        }
        $result = psql $DatabaseUrl -c $Query 2>&1
        return $result
    }
}

# 1. Check table structure (bank_id columns)
Write-Host "1. Checking table structure for bank_id columns..." -ForegroundColor Yellow
Write-Host ""

$tables = @("reports", "transactions")

foreach ($table in $tables) {
    Write-Host "   Checking $table..." -ForegroundColor Cyan
    
    $query = "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '$table' AND column_name = 'bank_id';"
    $result = Invoke-Sql -Query $query
    
    if ($result -match "bank_id") {
        Write-Host "   [OK] $table has bank_id column" -ForegroundColor Green
        if ($result -match "uuid") {
            Write-Host "      Type: UUID" -ForegroundColor Gray
        }
    } else {
        Write-Host "   [FAIL] $table missing bank_id column" -ForegroundColor Red
    }
}

Write-Host ""

# 2. Check RLS is enabled
Write-Host "2. Checking RLS is enabled on tables..." -ForegroundColor Yellow
Write-Host ""

foreach ($table in $tables) {
    $query = "SELECT relname, relrowsecurity FROM pg_class WHERE relname = '$table';"
    $result = Invoke-Sql -Query $query
    
    if ($result -match "t" -or $result -match "true") {
        Write-Host "   [OK] RLS enabled on $table" -ForegroundColor Green
    } elseif ($result -match "f" -or $result -match "false") {
        Write-Host "   [FAIL] RLS NOT enabled on $table" -ForegroundColor Red
    } else {
        Write-Host "   [WARNING] Could not determine RLS status for $table" -ForegroundColor Yellow
    }
}

Write-Host ""

# 3. Check RLS policies exist
Write-Host "3. Checking RLS policies..." -ForegroundColor Yellow
Write-Host ""

$query = "SELECT polname, tablename, polcmd FROM pg_policies WHERE tablename IN ('reports','transactions','transaction_volume') ORDER BY tablename, polname;"
$result = Invoke-Sql -Query $query

if ($result -match "polname") {
    Write-Host "   [OK] RLS policies found:" -ForegroundColor Green
    Write-Host ""
    # Parse and display policies
    $lines = $result -split "`n" | Where-Object { $_ -match "^\s+\|" -or $_ -match "polname" -or $_ -match "^\s+-" }
    foreach ($line in $lines) {
        if ($line -match "polname|tablename|polcmd" -and $line -notmatch "^\s+-") {
            Write-Host "   $line" -ForegroundColor Gray
        }
    }
    
    # Count policies
    $policyCount = ($result -split "`n" | Where-Object { $_ -match "^\s+\|" -and $_ -notmatch "polname" }).Count
    if ($policyCount -gt 0) {
        Write-Host ""
        Write-Host "   Total policies found: $policyCount" -ForegroundColor Green
    }
} else {
    Write-Host "   [FAIL] No RLS policies found" -ForegroundColor Red
    Write-Host "   Run migrations: .\scripts\run-migrations-ordered.ps1" -ForegroundColor Yellow
}

Write-Host ""

# 4. Check TimescaleDB hypertable (transaction_volume)
Write-Host "4. Checking TimescaleDB hypertable..." -ForegroundColor Yellow
Write-Host ""

$query = "SELECT hypertable_name FROM timescaledb_information.hypertables WHERE hypertable_name = 'transaction_volume';"
$result = Invoke-Sql -Query $query

if ($result -match "transaction_volume") {
    Write-Host "   [OK] transaction_volume hypertable exists" -ForegroundColor Green
    
    # Check if it has bank_id
    $query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'transaction_volume' AND column_name = 'bank_id';"
    $result = Invoke-Sql -Query $query
    if ($result -match "bank_id") {
        Write-Host "   [OK] transaction_volume has bank_id column" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] transaction_volume missing bank_id column" -ForegroundColor Red
    }
} else {
    Write-Host "   [WARNING] transaction_volume hypertable not found" -ForegroundColor Yellow
    Write-Host "   Run TimescaleDB migration: infra/timescale/001_metrics_timeseries.sql" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To see detailed table structure:" -ForegroundColor Yellow
if ($useDocker) {
    Write-Host "  docker exec $containerName psql -U payscope -d payscope -c '\d+ reports'" -ForegroundColor Gray
    Write-Host "  docker exec $containerName psql -U payscope -d payscope -c '\d+ transactions'" -ForegroundColor Gray
} else {
    Write-Host "  psql `$DATABASE_URL -c '\d+ reports'" -ForegroundColor Gray
    Write-Host "  psql `$DATABASE_URL -c '\d+ transactions'" -ForegroundColor Gray
}
Write-Host ""



