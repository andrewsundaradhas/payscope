# Setup Kaggle API Token - Convert to kaggle.json format
# The Kaggle Python API requires username and key in kaggle.json format

param(
    [string]$ApiToken = "KGAT_49d11903a842d30ddd0789795c6e5169",
    [string]$Username = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kaggle API Token Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Username) {
    Write-Host "[INFO] To use the API token, you need:" -ForegroundColor Yellow
    Write-Host "  1. Your Kaggle username (email address)" -ForegroundColor White
    Write-Host "  2. The API token" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternatively, download kaggle.json from:" -ForegroundColor Cyan
    Write-Host "  https://www.kaggle.com/settings" -ForegroundColor White
    Write-Host ""
    Write-Host "The kaggle.json file contains both username and key." -ForegroundColor Gray
    exit 0
}

# Create .kaggle directory
$kaggleDir = "$env:USERPROFILE\.kaggle"
New-Item -ItemType Directory -Force -Path $kaggleDir | Out-Null

# Create kaggle.json
$kaggleJson = @{
    username = $Username
    key = $ApiToken
} | ConvertTo-Json

$kaggleJsonPath = "$kaggleDir\kaggle.json"
$kaggleJson | Out-File -FilePath $kaggleJsonPath -Encoding utf8

Write-Host "[OK] Created kaggle.json at: $kaggleJsonPath" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Cyan
Write-Host "  python datasets/download_and_prepare.py" -ForegroundColor White



