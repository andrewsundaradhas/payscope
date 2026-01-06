# PayScope Setup Script
# Interactive setup helper for PayScope deployment

param(
    [switch]$SkipChecks,
    [switch]$InstallDocker,
    [switch]$InstallPostgres
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PayScope Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run prerequisites check first
if (-not $SkipChecks) {
    Write-Host "Running prerequisites check..." -ForegroundColor Yellow
    & "$PSScriptRoot\check-prerequisites.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Please install missing prerequisites before continuing." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Check for .env file
$envFile = Join-Path $PSScriptRoot ".." ".env"
$envExample = Join-Path $PSScriptRoot ".." "env" "local.env.example"

if (-not (Test-Path $envFile)) {
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "✓ Created .env file at: $envFile" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠ IMPORTANT: Edit .env and set:" -ForegroundColor Yellow
        Write-Host "  - JWT_PRIVATE_KEY and JWT_PUBLIC_KEY (generate RSA keypair)" -ForegroundColor White
        Write-Host "  - PINECONE_API_KEY (if using Pinecone)" -ForegroundColor White
        Write-Host "  - All database/service credentials" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "✗ Could not find $envExample" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Check for docker-compose.yml
$composeFile = Join-Path $PSScriptRoot ".." "docker-compose.yml"
if (-not (Test-Path $composeFile)) {
    Write-Host ""
    Write-Host "⚠ docker-compose.yml not found" -ForegroundColor Yellow
    Write-Host "  You'll need to create a docker-compose.yml file" -ForegroundColor White
    Write-Host "  See infra/docker-compose.local.yml for reference" -ForegroundColor White
}

# Generate JWT keys helper
Write-Host ""
$generateKeys = Read-Host "Generate JWT keypair? (y/n)"
if ($generateKeys -eq "y" -or $generateKeys -eq "Y") {
    Write-Host "Generating RSA keypair for JWT..." -ForegroundColor Yellow
    
    # Check if openssl is available
    try {
        $opensslVersion = openssl version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $keysDir = Join-Path $PSScriptRoot ".." "keys"
            New-Item -ItemType Directory -Force -Path $keysDir | Out-Null
            
            $privateKey = Join-Path $keysDir "jwt_private.pem"
            $publicKey = Join-Path $keysDir "jwt_public.pem"
            
            openssl genrsa -out $privateKey 2048
            openssl rsa -in $privateKey -pubout -out $publicKey
            
            Write-Host "✓ Generated keys:" -ForegroundColor Green
            Write-Host "  Private: $privateKey" -ForegroundColor Gray
            Write-Host "  Public: $publicKey" -ForegroundColor Gray
            Write-Host ""
            Write-Host "⚠ Add these to your .env file:" -ForegroundColor Yellow
            Write-Host "  JWT_PRIVATE_KEY=<contents of jwt_private.pem>" -ForegroundColor White
            Write-Host "  JWT_PUBLIC_KEY=<contents of jwt_public.pem>" -ForegroundColor White
        } else {
            Write-Host "✗ OpenSSL not found. Install OpenSSL to generate keys." -ForegroundColor Red
            Write-Host "  Or generate keys manually using:" -ForegroundColor Yellow
            Write-Host "  openssl genrsa -out jwt_private.pem 2048" -ForegroundColor White
            Write-Host "  openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem" -ForegroundColor White
        }
    } catch {
        Write-Host "✗ OpenSSL not available. Install OpenSSL or generate keys manually." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review and configure .env file" -ForegroundColor White
Write-Host "2. Start services: docker compose up -d" -ForegroundColor White
Write-Host "3. Run migrations (see scripts/run-migrations.ps1)" -ForegroundColor White
Write-Host "4. Validate setup (see scripts/validate-setup.ps1)" -ForegroundColor White



