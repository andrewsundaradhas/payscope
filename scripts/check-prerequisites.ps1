# PayScope Prerequisites Checker
# Verifies system tools required for deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PayScope Prerequisites Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Function to check command availability
function Test-Command {
    param([string]$Command, [string]$Name, [string]$MinVersion = $null)
    
    Write-Host "Checking $Name..." -NoNewline
    
    try {
        $version = & $Command --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version) {
            Write-Host " ✓ FOUND" -ForegroundColor Green
            Write-Host "  Version: $($version -split "`n" | Select-Object -First 1)" -ForegroundColor Gray
            
            # Version check if specified
            if ($MinVersion) {
                # Basic version parsing (can be enhanced)
                Write-Host "  Note: Minimum required: $MinVersion" -ForegroundColor Yellow
            }
            return $true
        } else {
            Write-Host " ✗ NOT FOUND" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ✗ NOT FOUND" -ForegroundColor Red
        return $false
    }
}

# Check Python 3.11+
Write-Host "1. Python (3.11+ required)" -ForegroundColor Yellow
$pythonOk = Test-Command -Command "python" -Name "Python" -MinVersion "3.11"
if (-not $pythonOk) {
    Write-Host "   Download: https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "   Or use winget: winget install Python.Python.3.11" -ForegroundColor Cyan
    $allGood = $false
} else {
    # Check Python version
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "3\.(1[1-9]|[2-9][0-9]|\d{2,})") {
        Write-Host "   ✓ Python version is compatible" -ForegroundColor Green
    } elseif ($pythonVersion -match "3\.1[0-9]") {
        Write-Host "   ⚠ Python 3.10 detected; 3.11+ recommended" -ForegroundColor Yellow
    }
}
Write-Host ""

# Check Docker
Write-Host "2. Docker" -ForegroundColor Yellow
$dockerOk = Test-Command -Command "docker" -Name "Docker"
if (-not $dockerOk) {
    Write-Host "   Download Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    Write-Host "   Or use winget: winget install Docker.DockerDesktop" -ForegroundColor Cyan
    Write-Host "   Note: Docker Desktop includes Docker Compose" -ForegroundColor Gray
    $allGood = $false
}
Write-Host ""

# Check Docker Compose
Write-Host "3. Docker Compose" -ForegroundColor Yellow
$composeOk = Test-Command -Command "docker" -Name "Docker Compose" -MinVersion "v2"
if (-not $composeOk) {
    Write-Host "   Docker Compose is included with Docker Desktop" -ForegroundColor Cyan
    Write-Host "   Or use standalone: https://docs.docker.com/compose/install/" -ForegroundColor Cyan
    $allGood = $false
} else {
    # Try to get compose version
    try {
        $composeVersion = docker compose version 2>&1
        if ($composeVersion) {
            Write-Host "  Compose: $($composeVersion -split "`n" | Select-Object -First 1)" -ForegroundColor Gray
        }
    } catch {
        # Ignore
    }
}
Write-Host ""

# Check PostgreSQL client (psql)
Write-Host "4. PostgreSQL Client (psql)" -ForegroundColor Yellow
$psqlOk = Test-Command -Command "psql" -Name "PostgreSQL Client"
if (-not $psqlOk) {
    Write-Host "   Option 1 - Full PostgreSQL (includes psql):" -ForegroundColor Cyan
    Write-Host "     Download: https://www.postgresql.org/download/windows/" -ForegroundColor Cyan
    Write-Host "     Or use winget: winget install PostgreSQL.PostgreSQL" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Option 2 - Client tools only:" -ForegroundColor Cyan
    Write-Host "     Use Chocolatey: choco install postgresql" -ForegroundColor Cyan
    Write-Host "     Or download standalone: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads" -ForegroundColor Cyan
    $allGood = $false
}
Write-Host ""

# Check Poetry (optional but recommended)
Write-Host "5. Poetry (Python dependency manager)" -ForegroundColor Yellow
$poetryOk = Test-Command -Command "poetry" -Name "Poetry"
if (-not $poetryOk) {
    Write-Host "   Recommended for Python dependency management" -ForegroundColor Yellow
    Write-Host "   Install: pip install poetry==1.8.5" -ForegroundColor Cyan
    Write-Host "   Or: (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -" -ForegroundColor Cyan
    Write-Host "   Note: Poetry is optional if using pip + requirements.txt" -ForegroundColor Gray
} else {
    Write-Host "   ✓ Poetry is available" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✓ All required tools are installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Set up .env file (copy from env/local.env.example)" -ForegroundColor White
    Write-Host "2. Start services: docker compose up -d" -ForegroundColor White
    Write-Host "3. Run migrations: psql \$DATABASE_URL -f infra/postgres/001_canonical_facts.sql" -ForegroundColor White
    Write-Host "4. Upload test data and validate" -ForegroundColor White
} else {
    Write-Host "✗ Some required tools are missing" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install the missing tools above, then run this script again." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

exit $(if ($allGood) { 0 } else { 1 })



