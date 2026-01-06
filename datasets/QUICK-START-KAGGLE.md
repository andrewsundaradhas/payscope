# Quick Start: Kaggle API Token Setup

You have your Kaggle API token: `KGAT_49d11903a842d30ddd0789795c6e5169`

## Quick Setup (PowerShell)

### Option 1: Set for Current Session Only
```powershell
$env:KAGGLE_API_TOKEN = "KGAT_49d11903a842d30ddd0789795c6e5169"
```

### Option 2: Use Setup Script (Recommended)
```powershell
.\datasets\setup-kaggle-env.ps1
```

This script will:
- Set the token for current session
- Test the connection
- Show you how to make it permanent

### Option 3: Make It Permanent (User Environment Variable)
```powershell
[System.Environment]::SetEnvironmentVariable('KAGGLE_API_TOKEN', 'KGAT_49d11903a842d30ddd0789795c6e5169', 'User')
```

**Note:** You'll need to restart PowerShell or your IDE for permanent changes to take effect.

## Add to .env File (Project-Specific)

Add this line to your `.env` file:
```bash
KAGGLE_API_TOKEN=KGAT_49d11903a842d30ddd0789795c6e5169
```

## Verify Setup

Test that it's working:
```powershell
# Install kaggle if needed
pip install kaggle

# Test connection
kaggle datasets list --max-size 5
```

Or test in Python:
```python
import os
os.environ['KAGGLE_API_TOKEN'] = 'KGAT_49d11903a842d30ddd0789795c6e5169'
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
print("OK: Connected!")
```

## Run Dataset Download

Once the token is set, you can run:
```powershell
python datasets/download_and_prepare.py
```

## Troubleshooting

### "401 Unauthorized" Error
- Make sure the token is set correctly: `echo $env:KAGGLE_API_TOKEN`
- Verify token hasn't expired (create new one at https://www.kaggle.com/settings if needed)

### "Command not found: kaggle"
- Install: `pip install kaggle`
- Or use Python API directly (the download script handles this)

### Token Not Persisting
- For permanent setup, use Option 3 above or add to PowerShell profile
- Check system environment variables in Windows Settings

## Next Steps

✅ Token configured  
→ Run: `python datasets/download_and_prepare.py`  
→ Then: `python datasets/run_e2e.py`



