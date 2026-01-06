# Add JWT keys to .env file
# Handles multiline PEM keys properly for .env format

param(
    [string]$EnvFile = ".env",
    [string]$PrivateKeyFile = "jwt_private.pem",
    [string]$PublicKeyFile = "jwt_public.pem",
    [string]$ExampleFile = "env/local.env.example"
)

$ErrorActionPreference = "Stop"

Write-Host "Adding JWT keys to .env file..." -ForegroundColor Yellow
Write-Host ""

# Check if key files exist
if (-not (Test-Path $PrivateKeyFile)) {
    Write-Host "✗ Private key file not found: $PrivateKeyFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PublicKeyFile)) {
    Write-Host "✗ Public key file not found: $PublicKeyFile" -ForegroundColor Red
    exit 1
}

# Read key files
$privateKeyContent = Get-Content $PrivateKeyFile -Raw
$publicKeyContent = Get-Content $PublicKeyFile -Raw

# Trim whitespace
$privateKeyContent = $privateKeyContent.Trim()
$publicKeyContent = $publicKeyContent.Trim()

# Create .env file if it doesn't exist
if (-not (Test-Path $EnvFile)) {
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    if (Test-Path $ExampleFile) {
        Copy-Item $ExampleFile $EnvFile
        Write-Host "✓ Created .env from $ExampleFile" -ForegroundColor Green
    } else {
        Write-Host "⚠ Example file not found, creating empty .env" -ForegroundColor Yellow
        New-Item -ItemType File -Path $EnvFile | Out-Null
    }
    Write-Host ""
}

# Read existing .env content
$envContent = Get-Content $EnvFile -Raw
if (-not $envContent) {
    $envContent = ""
}

# Remove existing JWT key entries (regex to match JWT_PRIVATE_KEY or JWT_PUBLIC_KEY lines)
# We'll rebuild the file
$lines = if ($envContent) { $envContent -split "`r?`n" } else { @() }

$newLines = @()
$inJwtSection = $false

foreach ($line in $lines) {
    # Skip existing JWT key lines
    if ($line -match "^JWT_(PRIVATE|PUBLIC)_KEY\s*=.*$") {
        continue
    }
    # Skip empty line after JWT section if this is the first non-JWT line
    if ($inJwtSection -and $line.Trim() -eq "" -and $newLines.Count -gt 0 -and $newLines[-1] -match "^# JWT") {
        $inJwtSection = $false
        continue
    }
    $newLines += $line
}

# Find insertion point (after last non-empty, non-comment line, or at end)
$insertIndex = $newLines.Count
for ($i = $newLines.Count - 1; $i -ge 0; $i--) {
    $trimmed = $newLines[$i].Trim()
    if ($trimmed -ne "" -and -not $trimmed.StartsWith("#")) {
        $insertIndex = $i + 1
        break
    }
}

# Build final content
$finalLines = @()
for ($i = 0; $i -lt $insertIndex; $i++) {
    $finalLines += $newLines[$i]
}

# Add empty line before JWT section if needed
if ($finalLines.Count -gt 0 -and $finalLines[-1].Trim() -ne "") {
    $finalLines += ""
}

# Add JWT keys section
# For .env files, we'll store PEM keys with escaped newlines
# Format: KEY="line1\nline2\nline3"
# python-dotenv (used by pydantic-settings) supports this format
$privateKeyEscaped = $privateKeyContent -replace "`r?`n", "\n"
$publicKeyEscaped = $publicKeyContent -replace "`r?`n", "\n"

$finalLines += "# JWT Keys (PEM format with escaped newlines)"
$finalLines += "JWT_PRIVATE_KEY=`"$privateKeyEscaped`""
$finalLines += "JWT_PUBLIC_KEY=`"$publicKeyEscaped`""

# Add remaining lines
for ($i = $insertIndex; $i -lt $newLines.Count; $i++) {
    $finalLines += $newLines[$i]
}

# Write back to file
$finalContent = $finalLines -join "`n"
# Ensure file ends with newline
if (-not $finalContent.EndsWith("`n")) {
    $finalContent += "`n"
}
[System.IO.File]::WriteAllText((Resolve-Path $EnvFile -ErrorAction SilentlyContinue) -or $EnvFile, $finalContent, [System.Text.Encoding]::UTF8)

Write-Host "✓ Added JWT keys to $EnvFile" -ForegroundColor Green
Write-Host ""
Write-Host "Keys are stored with escaped newlines (\n) for .env compatibility." -ForegroundColor Cyan
Write-Host "This format works with python-dotenv (used by pydantic-settings)." -ForegroundColor Cyan
Write-Host ""

# Verify keys were added
$verifyContent = Get-Content $EnvFile -Raw
if ($verifyContent -match 'JWT_PRIVATE_KEY=' -and $verifyContent -match 'JWT_PUBLIC_KEY=') {
    Write-Host '[OK] Verification: JWT keys found in .env file' -ForegroundColor Green
} else {
    Write-Host '[WARNING] Could not verify keys were added correctly' -ForegroundColor Yellow
}
