# Non-interactive script to configure Pinecone and Neo4j in .env file
# Usage: .\scripts\configure-dependencies.ps1 -PineconeApiKey "key" -PineconeIndexName "index" -Neo4jPassword "pass"

param(
    [string]$EnvFile = ".env",
    [string]$PineconeApiKey = "",
    [string]$PineconeIndexName = "payscope-index",
    [string]$Neo4jPassword = ""
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
        Write-Host "Creating .env from example..." -ForegroundColor Yellow
        if (Test-Path "env/local.env.example") {
            Copy-Item "env/local.env.example" $envPath
            Write-Host "[OK] Created .env from example" -ForegroundColor Green
        } else {
            New-Item -ItemType File -Path $envPath | Out-Null
            Write-Host "[OK] Created empty .env file" -ForegroundColor Green
        }
    }
}

Write-Host "Configuring dependencies in: $envPath" -ForegroundColor Yellow
Write-Host ""

# Read current .env content
$envContent = Get-Content $envPath -Raw -ErrorAction SilentlyContinue
$lines = if ($envContent) { $envContent -split "`r?`n" } else { @() }

# Function to update or add env var
function Update-EnvVar {
    param([string]$Key, [string]$Value, [string]$Comment = "")
    
    $newLines = @()
    $found = $false
    
    foreach ($line in $script:lines) {
        if ($line -match "^$Key\s*=") {
            if ($Value) {
                $newLines += "$Key=$Value"
            }
            $found = $true
        } else {
            $newLines += $line
        }
    }
    
    if (-not $found -and $Value) {
        if ($Comment) {
            $newLines += "# $Comment"
        }
        $newLines += "$Key=$Value"
    }
    
    $script:lines = $newLines
}

# Pinecone Configuration
if ($PineconeApiKey) {
    Update-EnvVar -Key "PINECONE_API_KEY" -Value $PineconeApiKey -Comment "Pinecone API Key"
    Write-Host "[OK] PINECONE_API_KEY configured" -ForegroundColor Green
} else {
    Write-Host "[SKIP] PINECONE_API_KEY not provided (use -PineconeApiKey parameter)" -ForegroundColor Yellow
}

if ($PineconeIndexName) {
    Update-EnvVar -Key "PINECONE_INDEX_NAME" -Value $PineconeIndexName -Comment "Pinecone Index Name"
    Write-Host "[OK] PINECONE_INDEX_NAME set to: $PineconeIndexName" -ForegroundColor Green
}

# Neo4j Configuration
if ($Neo4jPassword) {
    Update-EnvVar -Key "NEO4J_PASSWORD" -Value $Neo4jPassword -Comment "Neo4j Password"
    Write-Host "[OK] NEO4J_PASSWORD configured" -ForegroundColor Green
} else {
    Write-Host "[SKIP] NEO4J_PASSWORD not provided (use -Neo4jPassword parameter)" -ForegroundColor Yellow
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
if ($PineconeApiKey) {
    Write-Host "1. Create Pinecone index:" -ForegroundColor White
    Write-Host "   python scripts/create-pinecone-index.py" -ForegroundColor Cyan
    Write-Host ""
}
Write-Host "2. Start services:" -ForegroundColor White
Write-Host "   cd infra" -ForegroundColor Cyan
Write-Host "   docker compose -f docker-compose.local.yml up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Verify dependencies:" -ForegroundColor White
Write-Host "   python scripts/check-dependencies.py" -ForegroundColor Cyan
Write-Host ""



