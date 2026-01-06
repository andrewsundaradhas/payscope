# Setup Kaggle API Token as Environment Variable (Windows)
# This is an alternative to using kaggle.json file

param(
    [string]$ApiToken = "KGAT_49d11903a842d30ddd0789795c6e5169"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kaggle API Token Setup (Environment Variable)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variable for current session
$env:KAGGLE_API_TOKEN = $ApiToken
Write-Host "[OK] Set KAGGLE_API_TOKEN for current PowerShell session" -ForegroundColor Green
Write-Host ""

# Test connection
Write-Host "Testing Kaggle API connection..." -ForegroundColor Cyan
try {
    # Install kaggle if needed
    $kaggleCheck = python -m pip show kaggle 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Installing kaggle package..." -ForegroundColor Yellow
        python -m pip install kaggle
    }

    # Test API
    $testResult = kaggle datasets list --max-size 1 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Kaggle API connection successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Token is set for this session. To make it permanent:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Option 1: Add to your PowerShell profile" -ForegroundColor Cyan
        Write-Host '  Add this line to: $PROFILE' -ForegroundColor Gray
        Write-Host '  $env:KAGGLE_API_TOKEN="KGAT_49d11903a842d30ddd0789795c6e5169"' -ForegroundColor White
        Write-Host ""
        Write-Host "Option 2: Add to system environment variables (permanent)" -ForegroundColor Cyan
        Write-Host "  [System.Environment]::SetEnvironmentVariable('KAGGLE_API_TOKEN', '$ApiToken', 'User')" -ForegroundColor White
        Write-Host ""
        Write-Host "Option 3: Add to .env file (for this project)" -ForegroundColor Cyan
        Write-Host "  Add: KAGGLE_API_TOKEN=$ApiToken" -ForegroundColor White
    } else {
        Write-Host "[WARNING] API test failed:" -ForegroundColor Yellow
        Write-Host $testResult -ForegroundColor Gray
    }
} catch {
    Write-Host "[WARNING] Could not test API: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Current session setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Yellow
Write-Host "  python datasets/download_and_prepare.py" -ForegroundColor White
Write-Host ""



