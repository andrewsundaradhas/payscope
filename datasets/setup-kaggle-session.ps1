# Set Kaggle credentials for current PowerShell session
# Run this before running dataset download scripts

$env:KAGGLE_USERNAME = "andrewsundaradhas"
$env:KAGGLE_KEY = "KGAT_7e8e69bea5d3d77890c99ebbc963f90b"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kaggle Credentials Set (Current Session)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] KAGGLE_USERNAME = $env:KAGGLE_USERNAME" -ForegroundColor Green
Write-Host "[OK] KAGGLE_KEY = $($env:KAGGLE_KEY.Substring(0,10))..." -ForegroundColor Green
Write-Host ""

# Test connection
Write-Host "Testing Kaggle API connection..." -ForegroundColor Cyan
try {
    python -c "from kaggle.api.kaggle_api_extended import KaggleApi; api = KaggleApi(); api.authenticate(); print('OK: Connected!')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Kaggle API connection successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run:" -ForegroundColor Yellow
        Write-Host "  python datasets/download_and_prepare.py" -ForegroundColor White
    } else {
        Write-Host "[WARNING] Connection test failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] Could not test connection" -ForegroundColor Yellow
}

Write-Host ""



