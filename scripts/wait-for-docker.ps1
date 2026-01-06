# Wait for Docker to be available and then start services

param(
    [int]$MaxWaitSeconds = 60,
    [switch]$AutoStart
)

$ErrorActionPreference = "Stop"

Write-Host "Waiting for Docker to be available..." -ForegroundColor Yellow

$waited = 0
$dockerAvailable = $false

while ($waited -lt $MaxWaitSeconds) {
    try {
        $version = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerAvailable = $true
            Write-Host "[OK] Docker is available: $version" -ForegroundColor Green
            break
        }
    } catch {
        # Docker not available yet
    }
    
    Start-Sleep -Seconds 2
    $waited += 2
    Write-Host "  Waiting... ($waited/$MaxWaitSeconds seconds)" -ForegroundColor Gray
}

if (-not $dockerAvailable) {
    Write-Host "[FAIL] Docker not available after $MaxWaitSeconds seconds" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "2. Start Docker Desktop application" -ForegroundColor White
    Write-Host "3. Wait for Docker to fully start (whale icon in system tray)" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    exit 1
}

# Check if Docker daemon is running
try {
    $info = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Docker is installed but daemon is not running" -ForegroundColor Yellow
        Write-Host "Please start Docker Desktop application" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[WARNING] Docker daemon may not be running" -ForegroundColor Yellow
    Write-Host "Please start Docker Desktop application" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Docker daemon is running" -ForegroundColor Green
Write-Host ""

if ($AutoStart) {
    Write-Host "Starting PayScope services..." -ForegroundColor Yellow
    Push-Location infra
    try {
        docker compose -f docker-compose.local.yml up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[OK] Services started successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Waiting 10 seconds for services to initialize..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
            Write-Host ""
            Write-Host "Checking service status..." -ForegroundColor Yellow
            docker compose -f docker-compose.local.yml ps
        } else {
            Write-Host "[FAIL] Failed to start services" -ForegroundColor Red
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Docker is ready! You can now start services:" -ForegroundColor Green
    Write-Host "  cd infra" -ForegroundColor Cyan
    Write-Host "  docker compose -f docker-compose.local.yml up -d" -ForegroundColor Cyan
}



