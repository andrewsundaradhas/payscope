# Running Dataset Pipeline Without Docker

You can download and prepare datasets **without Docker**, but you'll need Docker later for:
- Ingestion service (to upload datasets)
- Processing workers (to process data)
- Database services (PostgreSQL, Neo4j, Redis, MinIO)

## What You Can Do Now

### 1. Download & Prepare Datasets ✅
```powershell
python datasets/download_and_prepare.py
```

This will:
- Download datasets from Kaggle for banks 1-4
- Sample to manageable sizes (50k-150k rows)
- Save to `datasets/processed/bank_{id}/bank_{id}_processed.csv`

**No Docker required!** This only needs:
- Python
- Kaggle API credentials (already set)
- Internet connection

### 2. Generate Synthetic Bank 5 ✅
```powershell
python datasets/generate_synthetic_bank.py
```

Creates synthetic dataset by mixing banks 1-4.

### 3. Train Models Locally ✅ (Partial)
You can train ML models on the downloaded datasets:
```powershell
python datasets/train_ml_complete.py all
```

This will:
- Train fraud detection models (LightGBM)
- Train forecasting models (Prophet + NeuralProphet)
- Save models locally

**Note:** S3 upload will fail without MinIO/Docker, but models will be saved locally.

## What Requires Docker

These steps need Docker services running:

### Upload to Ingestion ❌
```powershell
python datasets/upload_to_ingestion.py all
```
**Needs:** Ingestion service, PostgreSQL, MinIO, Redis

### Full Processing Pipeline ❌
- Parsing via Celery workers
- Normalization and persistence
- Graph/vector database writes

**Needs:** All Docker services running

## Recommended Workflow

### Phase 1: Without Docker (Now)
1. ✅ Download datasets
2. ✅ Generate synthetic bank
3. ✅ Train models locally

### Phase 2: With Docker (Later)
1. Install Docker Desktop
2. Start services: `docker compose up -d`
3. Run migrations: `.\scripts\run-migrations.ps1`
4. Upload datasets: `python datasets/upload_to_ingestion.py all`
5. Process data: Wait for Celery jobs
6. Verify: Check admin endpoint

## Installing Docker

### Windows
1. Download: https://www.docker.com/products/docker-desktop/
2. Install Docker Desktop
3. Start Docker Desktop application
4. Verify: `docker --version`

### After Docker is Running
```powershell
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

## Summary

**Can do now (no Docker):**
- ✅ Download datasets from Kaggle
- ✅ Prepare and sample data
- ✅ Generate synthetic bank
- ✅ Train ML models (local only)

**Need Docker for:**
- ❌ Upload to ingestion service
- ❌ Process data through pipeline
- ❌ Persist to databases (Postgres, Neo4j, Pinecone)
- ❌ Run full E2E pipeline

**Recommendation:** Download datasets now, install Docker when ready to run the full pipeline.



