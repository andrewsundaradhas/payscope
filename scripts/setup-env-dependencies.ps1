# Interactive script to configure Pinecone and Neo4j in .env file

param(
    [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PayScope Environment Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$envPath = Resolve-Path $EnvFile -ErrorAction SilentlyContinue
if (-not $envPath) {
    $envPath = $EnvFile
    if (-not (Test-Path $envPath)) {
        Write-Host "[FAIL] .env file not found at $envPath" -ForegroundColor Red
        Write-Host "Run setup script first: .\scripts\setup.ps1" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Configuring dependencies in: $envPath" -ForegroundColor Yellow
Write-Host ""

# Read current .env content
$envContent = Get-Content $envPath -Raw
$lines = if ($envContent) { $envContent -split "`r?`n" } else { @() }

# Function to update or add env var
function Update-EnvVar {
    param([string]$Key, [string]$Value, [string]$Comment = "")
    
    $newLines = @()
    $found = $false
    
    foreach ($line in $lines) {
        if ($line -match "^$Key\s*=") {
            $newLines += "$Key=$Value"
            $found = $true
        } else {
            $newLines += $line
        }
    }
    
    if (-not $found) {
        if ($Comment) {
            $newLines += "# $Comment"
        }
        $newLines += "$Key=$Value"
    }
    
    $script:lines = $newLines
}

# Pinecone Configuration
Write-Host "1. Pinecone Configuration" -ForegroundColor Yellow
Write-Host "   Get your API key from: https://www.pinecone.io/" -ForegroundColor Gray
Write-Host ""

$pineconeKey = Read-Host "Enter PINECONE_API_KEY (or press Enter to skip)"
if ($pineconeKey) {
    Update-EnvVar -Key "PINECONE_API_KEY" -Value $pineconeKey -Comment "Pinecone API Key"
    Write-Host "[OK] PINECONE_API_KEY added" -ForegroundColor Green
} else {
    Write-Host "[SKIP] PINECONE_API_KEY not set" -ForegroundColor Yellow
}

$indexName = Read-Host "Enter PINECONE_INDEX_NAME (or press Enter to skip, default: payscope-index)"
if (-not $indexName) {
    $indexName = "payscope-index"
}
Update-EnvVar -Key "PINECONE_INDEX_NAME" -Value $indexName -Comment "Pinecone Index Name"
Write-Host "[OK] PINECONE_INDEX_NAME set to: $indexName" -ForegroundColor Green

Write-Host ""

# Neo4j Configuration
Write-Host "2. Neo4j Configuration" -ForegroundColor Yellow
Write-Host "   Set a secure password for Neo4j" -ForegroundColor Gray
Write-Host ""

$neo4jPassword = Read-Host "Enter NEO4J_PASSWORD (or press Enter to skip)"
if ($neo4jPassword) {
    Update-EnvVar -Key "NEO4J_PASSWORD" -Value $neo4jPassword -Comment "Neo4j Password"
    Write-Host "[OK] NEO4J_PASSWORD added" -ForegroundColor Green
} else {
    Write-Host "[SKIP] NEO4J_PASSWORD not set (will use default from docker-compose)" -ForegroundColor Yellow
}

Write-Host ""

# Write updated .env file
$finalContent = $lines -join "`n"
if (-not $finalContent.EndsWith("`n")) {
    $finalContent += "`n"
}
[System.IO.File]::WriteAllText($envPath, $finalContent, [System.Text.Encoding]::UTF8)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[OK] .env file updated!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create Pinecone index:" -ForegroundColor White
Write-Host "   python scripts/create-pinecone-index.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Start services:" -ForegroundColor White
Write-Host "   docker compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Verify dependencies:" -ForegroundColor White
Write-Host "   python scripts/check-dependencies.py" -ForegroundColor Cyan
Write-Host ""



