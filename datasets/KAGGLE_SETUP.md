# Kaggle API Setup Guide

## Quick Setup for Gmail-based Kaggle Account

### Step 1: Download Kaggle API Credentials

1. Go to https://www.kaggle.com
2. Sign in with your Gmail account
3. Navigate to your account settings:
   - Click your profile picture (top right)
   - Click "Settings" or "Account"
4. Scroll down to the **API** section
5. Click **"Create New API Token"** or **"Download API Token"**
6. This downloads a file named `kaggle.json`

### Step 2: Place Credentials File

**Windows:**
```powershell
# Create the .kaggle directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kaggle"

# Copy your downloaded kaggle.json to the .kaggle directory
Copy-Item "C:\Users\speak\Downloads\kaggle.json" "$env:USERPROFILE\.kaggle\kaggle.json"

# Set secure permissions (Windows may require additional steps)
```

**Linux/Mac:**
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

### Step 3: Verify Setup

Test your Kaggle API connection:

```bash
# Install kaggle package if not already installed
pip install kaggle

# Test API access
kaggle datasets list --max-size 10
```

If you see a list of datasets, you're all set!

### Alternative: Environment Variables

If you prefer not to use the JSON file, you can set environment variables instead:

**Windows PowerShell:**
```powershell
# Set environment variables (session-only)
$env:KAGGLE_USERNAME = "your_gmail_address@gmail.com"
$env:KAGGLE_KEY = "your_api_key_from_kaggle_json"

# Or add to .env file:
# KAGGLE_USERNAME=your_gmail_address@gmail.com
# KAGGLE_KEY=your_api_key_from_kaggle_json
```

**Linux/Mac:**
```bash
export KAGGLE_USERNAME="your_gmail_address@gmail.com"
export KAGGLE_KEY="your_api_key_from_kaggle_json"
```

### Step 4: Run Dataset Download

Once credentials are set up, run:

```bash
python datasets/download_and_prepare.py
```

## Troubleshooting

### "403 Forbidden" Error
- Verify your Kaggle account is activated
- Check that you've accepted Kaggle's terms of service
- Ensure the API token is valid (create a new one if needed)

### "401 Unauthorized" Error
- Verify `kaggle.json` is in `~/.kaggle/` (or `%USERPROFILE%\.kaggle\` on Windows)
- Check file permissions (should be readable only by you)
- Verify username and key match your Kaggle account

### "Dataset Not Found" Error
- Some datasets may require you to accept their terms on Kaggle first
- Visit the dataset page on Kaggle and click "I Understand and Accept"

### Finding Your API Credentials

Your `kaggle.json` file contains:
```json
{
  "username": "your_gmail@gmail.com",
  "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

**Never commit this file to Git!** It's already in `.gitignore`.

## Required Datasets

Make sure you've accepted terms for these datasets on Kaggle:
- `mlg-ulb/creditcardfraud` (Bank 1)
- `c/ieee-fraud-detection` (Bank 2)
- `ealaxi/paysim1` (Bank 3)
- `olistbr/brazilian-ecommerce` (Bank 4)

Visit each dataset page and click "Download" or "I Understand and Accept" if prompted.

## Next Steps

Once Kaggle API is configured:
1. ✅ Run `python datasets/download_and_prepare.py`
2. ✅ Run `python datasets/generate_synthetic_bank.py`
3. ✅ Run `python datasets/run_e2e.py` for full pipeline



