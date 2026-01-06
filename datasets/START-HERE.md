# Start Here - Quick Setup Guide

## ✅ Kaggle API Configured

Your Kaggle credentials are now set up at:
`C:\Users\speak\.kaggle\kaggle.json`

Username: `andrewsundaradhas`

## 🚀 Next Steps

### 1. Start Docker Services

```powershell
docker compose up -d
```

This starts:
- PostgreSQL/TimescaleDB
- Redis
- MinIO
- Neo4j
- Ingestion service
- API service
- Processing worker

### 2. Run Database Migrations

```powershell
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"
.\scripts\run-migrations.ps1
```

### 3. Download & Process Datasets

**Option A: Run Everything (Recommended)**
```bash
python datasets/run_e2e.py
```

This will:
- Download datasets from Kaggle (banks 1-4)
- Generate synthetic bank 5
- Upload to ingestion service
- Wait for processing
- Train ML models
- Validate results

**Option B: Step by Step**

```bash
# Step 1: Download datasets
python datasets/download_and_prepare.py

# Step 2: Generate synthetic bank
python datasets/generate_synthetic_bank.py

# Step 3: Upload to ingestion
python datasets/upload_to_ingestion.py all

# Step 4: Train models
python datasets/train_ml_complete.py all
```

### 4. Verify Setup

Check admin endpoint (requires admin JWT):
```bash
curl http://localhost:8000/admin/validate-datasets
```

Or check services:
```bash
curl http://localhost:8080/health  # Ingestion
curl http://localhost:8000/health  # API
```

## 📊 Expected Results

After running E2E pipeline:

**Datasets:**
- Bank 1: ~100k rows (Credit Card Fraud Detection)
- Bank 2: ~150k rows (IEEE-CIS Fraud Detection)
- Bank 3: ~120k rows (PaySim)
- Bank 4: ~100k rows (Olist Brazilian E-commerce)
- Bank 5: ~100k rows (Synthetic mixed)

**Models:**
- Fraud detection models for each bank
- Forecasting models (Prophet + NeuralProphet)
- Saved to: `datasets/processed/bank_{id}/models/`
- Uploaded to S3/MinIO

**Data Stores:**
- Postgres: Transactions, reports per bank_id
- TimescaleDB: Time-series aggregates
- Neo4j: Graph nodes and edges
- Pinecone: Vector embeddings

## 🔧 Troubleshooting

### Kaggle API Errors
- Verify credentials: Check `~/.kaggle/kaggle.json` exists
- Test connection: `python -c "from kaggle.api.kaggle_api_extended import KaggleApi; KaggleApi().authenticate()"`

### Services Not Running
- Check Docker: `docker compose ps`
- View logs: `docker compose logs -f`
- Restart: `docker compose restart`

### Database Connection Issues
- Verify PostgreSQL is running: `docker compose ps postgres`
- Check DATABASE_URL in `.env`
- Test connection: `docker exec postgres psql -U payscope -d payscope -c "SELECT 1"`

### Processing Timeout
- Check Celery worker: `docker compose logs worker`
- Increase wait time in `upload_to_ingestion.py` if needed
- Verify all dependencies are accessible

## 📚 Documentation

- `datasets/README.md` - Complete dataset guide
- `datasets/ML_TRAINING_README.md` - ML training details
- `datasets/STATUS.md` - Current status and checklist
- `scripts/README.md` - Setup scripts guide

## ✨ You're Ready!

Everything is configured. Just run:
```bash
python datasets/run_e2e.py
```

Happy training! 🚀



