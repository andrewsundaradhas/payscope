# Quick Command Reference

## Setup & Prerequisites

### Set Kaggle Credentials (Each Session)
```powershell
.\datasets\setup-kaggle-session.ps1
```

### Check Prerequisites
```powershell
.\scripts\check-prerequisites.ps1
```

### Start Docker Services
```powershell
docker compose up -d
```

### Check Service Status
```powershell
docker compose ps
```

### View Service Logs
```powershell
docker compose logs -f
```

## Database Setup

### Run Migrations
```powershell
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"
.\scripts\run-migrations.ps1
```

### Verify RLS & bank_id
```powershell
.\scripts\verify-rls.ps1
```

## Dataset Pipeline

### Download Datasets Only
```powershell
python datasets/download_and_prepare.py
```

### Generate Synthetic Bank 5
```powershell
python datasets/generate_synthetic_bank.py
```

### Upload to Ingestion
```powershell
python datasets/upload_to_ingestion.py all
```

### Train ML Models
```powershell
python datasets/train_ml_complete.py all
```

### Run Everything (E2E)
```powershell
python datasets/run_e2e.py
```

### Run E2E with Options
```powershell
# Skip download (use existing datasets)
python datasets/run_e2e.py --skip-download

# Skip upload (already ingested)
python datasets/run_e2e.py --skip-upload

# Skip training (models already trained)
python datasets/run_e2e.py --skip-training
```

## Validation & Testing

### Validate Setup
```powershell
.\scripts\validate-setup.ps1
```

### Check Dependencies
```powershell
python scripts/check-dependencies.py
```

### Test API Endpoints
```powershell
curl http://localhost:8000/health
curl http://localhost:8080/health
```

### Validate Datasets (Admin)
```powershell
# Requires admin JWT token
curl -H "Authorization: Bearer <token>" http://localhost:8000/admin/validate-datasets
```

## Troubleshooting

### Restart Services
```powershell
docker compose restart
```

### Rebuild Services
```powershell
docker compose up -d --build
```

### Clean Start
```powershell
docker compose down
docker compose up -d
```

### Check Logs
```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f ingestion
docker compose logs -f worker
docker compose logs -f postgres
```

## Environment Variables

### Set for Session
```powershell
$env:KAGGLE_USERNAME = "andrewsundaradhas"
$env:KAGGLE_KEY = "KGAT_7e8e69bea5d3d77890c99ebbc963f90b"
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"
```

### Make Permanent (User Environment)
```powershell
[System.Environment]::SetEnvironmentVariable('KAGGLE_USERNAME', 'andrewsundaradhas', 'User')
[System.Environment]::SetEnvironmentVariable('KAGGLE_KEY', 'KGAT_7e8e69bea5d3d77890c99ebbc963f90b', 'User')
```

## Output Locations

- **Datasets**: `datasets/processed/bank_{id}/`
- **Models**: `datasets/processed/bank_{id}/models/`
- **Training Summary**: `datasets/ml_training_summary.json`
- **Logs**: Check Docker logs or service output



