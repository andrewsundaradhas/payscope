# Start PayScope services using docker-compose

param(
    [switch]$Build,
    [switch]$Detached = $true
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting PayScope Services" -ForegroundColor Cyan
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
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "2. Start Docker Desktop application" -ForegroundColor White
    Write-Host "3. Wait for Docker to fully start" -ForegroundColor White
    exit 1
}

# Check Docker daemon
try {
    docker info | Out-Null
    Write-Host "[OK] Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Docker daemon is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop application" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found" -ForegroundColor Yellow
    Write-Host "Creating from example..." -ForegroundColor Yellow
    if (Test-Path "env/local.env.example") {
        Copy-Item "env/local.env.example" ".env"
        Write-Host "[OK] Created .env from example" -ForegroundColor Green
        Write-Host "[WARNING] Please configure .env with your credentials" -ForegroundColor Yellow
    } else {
        Write-Host "[FAIL] Cannot create .env - example file not found" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Build compose command
$composeCmd = "docker compose"
if ($Build) {
    $composeCmd += " build"
}

if ($Detached) {
    $composeCmd += " up -d"
} else {
    $composeCmd += " up"
}

Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host "Command: $composeCmd" -ForegroundColor Gray
Write-Host ""

# Start services
Invoke-Expression $composeCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Services started successfully!" -ForegroundColor Green
    Write-Host ""
    
    if ($Detached) {
        Write-Host "Waiting 10 seconds for services to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        Write-Host ""
        Write-Host "Service status:" -ForegroundColor Yellow
        docker compose ps
        Write-Host ""
        Write-Host "View logs with:" -ForegroundColor Cyan
        Write-Host "  docker compose logs -f [service-name]" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "[FAIL] Failed to start services" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check logs with:" -ForegroundColor Yellow
    Write-Host "  docker compose logs" -ForegroundColor White
    exit 1
}



