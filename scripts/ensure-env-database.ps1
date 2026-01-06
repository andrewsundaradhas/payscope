# Ensure .env file has database configuration

param(
    [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"

Write-Host "Ensuring database configuration in .env..." -ForegroundColor Yellow
Write-Host ""

# Read current .env content
if (-not (Test-Path $EnvFile)) {
    Write-Host "[FAIL] .env file not found: $EnvFile" -ForegroundColor Red
    exit 1
}

$envContent = Get-Content $EnvFile -Raw
$lines = if ($envContent) { $envContent -split "`r?`n" } else { @() }

# Function to update or add env var
function Update-EnvVar {
    param([string]$Key, [string]$Value, [string]$Comment = "")
    
    $newLines = @()
    $found = $false
    
    foreach ($line in $script:lines) {
        # Match exact key at start of line (with optional whitespace)
        if ($line -match "^$Key\s*=") {
            $newLines += "$Key=$Value"
            $found = $true
        } else {
            $newLines += $line
        }
    }
    
    if (-not $found) {
        # Find insertion point (after Postgres section if exists, or after core config)
        $insertIndex = $newLines.Count
        for ($i = 0; $i -lt $newLines.Count; $i++) {
            if ($newLines[$i] -match "^# Postgres" -or $newLines[$i] -match "^# Database") {
                # Find end of postgres/database section
                for ($j = $i + 1; $j -lt $newLines.Count; $j++) {
                    if ($newLines[$j] -match "^# " -and $newLines[$j] -notmatch "^# (Postgres|Database)") {
                        $insertIndex = $j
                        break
                    }
                    if ($j -eq $newLines.Count - 1) {
                        $insertIndex = $j + 1
                    }
                }
                break
            }
            if ($newLines[$i] -match "^ENV=") {
                $insertIndex = $i + 3  # After ENV, empty line, and comment
            }
        }
        
        $finalLines = @()
        for ($i = 0; $i -lt $insertIndex; $i++) {
            $finalLines += $newLines[$i]
        }
        
        # Add comment if first database variable
        if ($Key -eq "DATABASE_URL" -and -not ($finalLines | Where-Object { $_ -match "^DATABASE" })) {
            if (-not ($finalLines[-1] -match "^# (Postgres|Database)")) {
                $finalLines += ""
                $finalLines += "# Postgres (local)"
            }
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

# Database connection strings (using 'postgres' hostname for Docker networking)
$dbDsn = "postgresql://payscope:payscope@postgres:5432/payscope"
$dbUrl = "postgresql://payscope:payscope@postgres:5432/payscope"

Update-EnvVar -Key "DATABASE_DSN" -Value $dbDsn -Comment "PostgreSQL connection string (for asyncpg)"
Update-EnvVar -Key "DATABASE_URL" -Value $dbUrl -Comment "PostgreSQL connection string (for SQLAlchemy)"

# Write back
$finalContent = $lines -join "`n"
if (-not $finalContent.EndsWith("`n")) {
    $finalContent += "`n"
}
[System.IO.File]::WriteAllText((Resolve-Path $EnvFile -ErrorAction SilentlyContinue) -or $EnvFile, $finalContent, [System.Text.Encoding]::UTF8)

Write-Host "[OK] Database configuration ensured in .env:" -ForegroundColor Green
Write-Host "  DATABASE_DSN=$dbDsn" -ForegroundColor Gray
Write-Host "  DATABASE_URL=$dbUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Using 'postgres' hostname (Docker service name)" -ForegroundColor Cyan



