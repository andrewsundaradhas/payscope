# PayScope Setup Validation Script
# Validates that all services are configured and accessible

param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$IngestionUrl = "http://localhost:8080",
    [string]$DatabaseUrl = $env:DATABASE_URL
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PayScope Setup Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param([string]$Url, [string]$Name)
    
    Write-Host "Testing $Name ($Url)..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
            Write-Host " ✓ REACHABLE" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ✗ HTTP $($response.StatusCode)" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host " ✗ NOT REACHABLE" -ForegroundColor Red
        return $false
    }
}

# Check Docker services
Write-Host "1. Docker Services" -ForegroundColor Yellow
try {
    $dockerPs = docker ps --format "{{.Names}}" 2>&1
    if ($LASTEXITCODE -eq 0 -and $dockerPs) {
        Write-Host "  Running containers:" -ForegroundColor Gray
        $dockerPs -split "`n" | ForEach-Object {
            if ($_) { Write-Host "    - $_" -ForegroundColor Gray }
        }
        
        $requiredServices = @("postgres", "redis", "minio", "neo4j")
        $runningServices = $dockerPs -split "`n" | Where-Object { $_ }
        
        $missingServices = @()
        foreach ($service in $requiredServices) {
            $found = $false
            foreach ($running in $runningServices) {
                if ($running -match $service) {
                    $found = $true
                    break
                }
            }
            if (-not $found) {
                $missingServices += $service
            }
        }
        
        if ($missingServices.Count -gt 0) {
            Write-Host "  ⚠ Missing services: $($missingServices -join ', ')" -ForegroundColor Yellow
            $allGood = $false
        } else {
            Write-Host "  ✓ All required services running" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✗ Docker not running or no containers found" -ForegroundColor Red
        Write-Host "    Start services: docker compose up -d" -ForegroundColor Yellow
        $allGood = $false
    }
} catch {
    Write-Host "  ✗ Docker not available: $_" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Test API endpoints
Write-Host "2. API Endpoints" -ForegroundColor Yellow
$apiOk = Test-HttpEndpoint -Url "$ApiUrl/docs" -Name "API Docs"
if (-not $apiOk) {
    Write-Host "  Start API service: docker compose up -d api" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Test Database connection
Write-Host "3. Database Connection" -ForegroundColor Yellow
if ($DatabaseUrl) {
    try {
        $dbTest = psql $DatabaseUrl -c "SELECT version();" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Database connection successful" -ForegroundColor Green
            
            # Check if migrations have been run
            $tablesCheck = psql $DatabaseUrl -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('reports','transactions');" 2>&1
            if ($tablesCheck -match "reports" -and $tablesCheck -match "transactions") {
                Write-Host "  ✓ Core tables exist" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Core tables not found. Run migrations: .\scripts\run-migrations.ps1" -ForegroundColor Yellow
                $allGood = $false
            }
            
            # Check RLS
            $rlsCheck = psql $DatabaseUrl -c "SELECT polname FROM pg_policies WHERE tablename='reports' LIMIT 1;" 2>&1
            if ($rlsCheck -match "polname") {
                Write-Host "  ✓ RLS policies found" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ RLS policies not found. Run migrations." -ForegroundColor Yellow
                $allGood = $false
            }
        } else {
            Write-Host "  ✗ Database connection failed" -ForegroundColor Red
            $allGood = $false
        }
    } catch {
        Write-Host "  ✗ Database connection failed: $_" -ForegroundColor Red
        Write-Host "    Set DATABASE_URL environment variable" -ForegroundColor Yellow
        $allGood = $false
    }
} else {
    Write-Host "  ⚠ DATABASE_URL not set" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Check .env file
Write-Host "4. Configuration" -ForegroundColor Yellow
$envFile = Join-Path (Split-Path -Parent $PSScriptRoot) ".env"
if (Test-Path $envFile) {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
    
    $envContent = Get-Content $envFile -Raw
    $requiredVars = @("DATABASE_URL", "JWT_PRIVATE_KEY", "JWT_PUBLIC_KEY")
    $missingVars = @()
    
    foreach ($var in $requiredVars) {
        if ($envContent -notmatch "$var\s*=") {
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Host "  ⚠ Missing variables: $($missingVars -join ', ')" -ForegroundColor Yellow
        $allGood = $false
    } else {
        Write-Host "  ✓ Required variables present" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ .env file not found" -ForegroundColor Red
    Write-Host "    Create from template: .\scripts\setup.ps1" -ForegroundColor Yellow
    $allGood = $false
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✓ Setup validation passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "System is ready for:" -ForegroundColor Yellow
    Write-Host "  - Uploading test data" -ForegroundColor White
    Write-Host "  - Running end-to-end tests" -ForegroundColor White
    Write-Host "  - Starting development workflow" -ForegroundColor White
} else {
    Write-Host "✗ Setup validation found issues" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the issues above before proceeding." -ForegroundColor Yellow
    exit 1
}
Write-Host "========================================" -ForegroundColor Cyan



