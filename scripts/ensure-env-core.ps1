# Ensure .env file has core configuration

param(
    [string]$EnvFile = ".env",
    [string]$ExampleFile = "env/local.env.example"
)

$ErrorActionPreference = "Stop"

Write-Host "Ensuring .env has core configuration..." -ForegroundColor Yellow
Write-Host ""

# Create .env from example if it doesn't exist
if (-not (Test-Path $EnvFile)) {
    Write-Host "Creating .env from example..." -ForegroundColor Yellow
    if (Test-Path $ExampleFile) {
        Copy-Item $ExampleFile $EnvFile
        Write-Host "[OK] Created .env from $ExampleFile" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Example file not found: $ExampleFile" -ForegroundColor Red
        exit 1
    }
}

# Read current .env content
$envContent = Get-Content $EnvFile -Raw
$lines = if ($envContent) { $envContent -split "`r?`n" } else { @() }

# Function to update or add env var
function Update-EnvVar {
    param([string]$Key, [string]$Value, [string]$Comment = "")
    
    $newLines = @()
    $found = $false
    
    foreach ($line in $script:lines) {
        if ($line -match "^$Key\s*=") {
            $newLines += "$Key=$Value"
            $found = $true
        } else {
            $newLines += $line
        }
    }
    
    if (-not $found) {
        # Add at the beginning after comments or at the top
        $insertIndex = 0
        for ($i = 0; $i -lt $newLines.Count; $i++) {
            if ($newLines[$i].Trim().StartsWith("#")) {
                $insertIndex = $i + 1
            } elseif ($newLines[$i].Trim() -eq "") {
                $insertIndex = $i + 1
            } else {
                break
            }
        }
        
        $finalLines = @()
        for ($i = 0; $i -lt $insertIndex; $i++) {
            $finalLines += $newLines[$i]
        }
        
        if ($Comment) {
            $finalLines += "# $Comment"
        }
        $finalLines += "$Key=$Value"
        
        for ($i = $insertIndex; $i -lt $newLines.Count; $i++) {
            $finalLines += $newLines[$i]
        }
        
        $script:lines = $finalLines
    } else {
        $script:lines = $newLines
    }
}

# Ensure core configuration
Update-EnvVar -Key "ENV" -Value "dev" -Comment "Environment: local | staging | production"
Update-EnvVar -Key "LOG_LEVEL" -Value "INFO" -Comment "Logging level: DEBUG | INFO | WARNING | ERROR"

# Write back
$finalContent = $lines -join "`n"
if (-not $finalContent.EndsWith("`n")) {
    $finalContent += "`n"
}
[System.IO.File]::WriteAllText((Resolve-Path $EnvFile -ErrorAction SilentlyContinue) -or $EnvFile, $finalContent, [System.Text.Encoding]::UTF8)

Write-Host "[OK] Core configuration ensured in .env:" -ForegroundColor Green
Write-Host "  ENV=dev" -ForegroundColor Gray
Write-Host "  LOG_LEVEL=INFO" -ForegroundColor Gray
Write-Host ""



