# Kaggle API Setup Script for Windows
# Automates placement of kaggle.json credentials file

param(
    [string]$KaggleJsonPath = "$env:USERPROFILE\Downloads\kaggle.json"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kaggle API Credentials Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if kaggle.json exists in default location
if (-not (Test-Path $KaggleJsonPath)) {
    Write-Host "[INFO] kaggle.json not found in default location." -ForegroundColor Yellow
    Write-Host "Expected: $KaggleJsonPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Go to: https://www.kaggle.com/settings" -ForegroundColor White
    Write-Host "  2. Click 'Create New API Token'" -ForegroundColor White
    Write-Host "  3. Download kaggle.json" -ForegroundColor White
    Write-Host ""
    Write-Host "Then run this script again with:" -ForegroundColor Cyan
    Write-Host "  .\datasets\setup-kaggle.ps1 -KaggleJsonPath `"path\to\kaggle.json`"" -ForegroundColor Gray
    exit 1
}

# Create .kaggle directory
$kaggleDir = "$env:USERPROFILE\.kaggle"
if (-not (Test-Path $kaggleDir)) {
    New-Item -ItemType Directory -Path $kaggleDir | Out-Null
    Write-Host "[OK] Created directory: $kaggleDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Directory exists: $kaggleDir" -ForegroundColor Green
}

# Copy kaggle.json
$targetPath = "$kaggleDir\kaggle.json"

# Check if file already exists
if (Test-Path $targetPath) {
    Write-Host ""
    Write-Host "[WARNING] kaggle.json already exists at: $targetPath" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "[SKIP] Keeping existing file" -ForegroundColor Yellow
        exit 0
    }
}

try {
    Copy-Item -Path $KaggleJsonPath -Destination $targetPath -Force
    Write-Host "[OK] Copied kaggle.json to: $targetPath" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to copy file: $_" -ForegroundColor Red
    exit 1
}

# Verify kaggle package is installed
Write-Host ""
Write-Host "Checking kaggle package..." -ForegroundColor Cyan
try {
    $kaggleVersion = python -m pip show kaggle 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Kaggle package is installed" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Installing kaggle package..." -ForegroundColor Yellow
        python -m pip install kaggle
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Kaggle package installed" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Failed to install kaggle package" -ForegroundColor Yellow
            Write-Host "Install manually: pip install kaggle" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[WARNING] Could not check/install kaggle package" -ForegroundColor Yellow
}

# Test API connection
Write-Host ""
Write-Host "Testing Kaggle API connection..." -ForegroundColor Cyan
try {
    $testResult = kaggle datasets list --max-size 1 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Kaggle API connection successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Setup complete! You can now run:" -ForegroundColor Cyan
        Write-Host "  python datasets/download_and_prepare.py" -ForegroundColor White
    } else {
        Write-Host "[WARNING] API test failed. Error:" -ForegroundColor Yellow
        Write-Host $testResult -ForegroundColor Gray
        Write-Host ""
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "  - Verify your Kaggle account is active" -ForegroundColor Gray
        Write-Host "  - Check that kaggle.json contains valid credentials" -ForegroundColor Gray
        Write-Host "  - Ensure you've accepted Kaggle's terms of service" -ForegroundColor Gray
    }
} catch {
    Write-Host "[WARNING] Could not test API (kaggle CLI may not be in PATH)" -ForegroundColor Yellow
    Write-Host "Test manually: kaggle datasets list --max-size 5" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan



