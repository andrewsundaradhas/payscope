# PayScope Dataset Loading & Training

This directory contains scripts to download, prepare, upload, and train on datasets for PayScope.

## Overview

The pipeline orchestrates:
1. **Download** - Downloads datasets from Kaggle (banks 1-4)
2. **Prepare** - Samples and normalizes datasets (50k-150k rows)
3. **Synthetic** - Generates synthetic bank 5 (mixed + augmented)
4. **Upload** - Uploads to ingestion service via `/upload` endpoint
5. **Train** - Trains baseline fraud detection and forecasting models
6. **Validate** - Validates data in Postgres, Neo4j, Pinecone

## Bank Assignments

- **Bank 1**: Kaggle Credit Card Fraud Detection
- **Bank 2**: IEEE-CIS Fraud Detection
- **Bank 3**: PaySim (synthetic payment lifecycle)
- **Bank 4**: Olist Brazilian E-commerce
- **Bank 5**: Synthetic mix of banks 1-4 (LLM-augmented)

## Prerequisites

### Python Dependencies

```bash
pip install pandas numpy kaggle requests lightgbm scikit-learn boto3 asyncpg neo4j pinecone-client
```

### Kaggle API Credentials

**Option 1: API Token (Recommended - Newer Method)**
```powershell
# Windows PowerShell (current session)
$env:KAGGLE_API_TOKEN="KGAT_49d11903a842d30ddd0789795c6e5169"

# Or use the setup script
.\datasets\setup-kaggle-env.ps1

# Permanent (User environment variable)
[System.Environment]::SetEnvironmentVariable('KAGGLE_API_TOKEN', 'KGAT_49d11903a842d30ddd0789795c6e5169', 'User')
```

**Option 2: Traditional kaggle.json File**
1. Download API credentials: https://www.kaggle.com/settings
2. Place `kaggle.json` in `~/.kaggle/` (or `%USERPROFILE%\.kaggle\` on Windows)
3. Or use: `.\datasets\setup-kaggle.ps1`

**Option 3: Environment Variables (Username/Key)**
```powershell
$env:KAGGLE_USERNAME="your_email@gmail.com"
$env:KAGGLE_KEY="your_api_key"
```

### Services Running

```bash
# Start all services
docker compose up -d

# Or start individually
docker compose up -d postgres redis minio neo4j
docker compose up -d ingestion api worker
```

### Environment Variables

Ensure `.env` file has:
```bash
DATABASE_URL=postgresql://payscope:payscope@localhost:5432/payscope
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=payscope
S3_SECRET_ACCESS_KEY=payscope-secret
S3_BUCKET=payscope-raw
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=payscope-index
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

## Usage

### Option 1: Run Everything (E2E)

```bash
python datasets/run_e2e.py
```

This will:
- Download and prepare all datasets
- Generate synthetic bank 5
- Upload all to ingestion
- Wait for processing
- Train models
- Validate data

### Option 2: Run Steps Individually

#### 1. Download & Prepare

```bash
python datasets/download_and_prepare.py
```

Downloads datasets from Kaggle, samples to manageable sizes, saves to:
- `datasets/processed/bank_1/bank_1_processed.csv`
- `datasets/processed/bank_2/bank_2_processed.csv`
- etc.

#### 2. Generate Synthetic Bank 5

```bash
python datasets/generate_synthetic_bank.py
```

Mixes 10-20% from each bank (1-4) and applies statistical perturbation.

#### 3. Upload to Ingestion

```bash
# Upload all banks
python datasets/upload_to_ingestion.py all

# Upload specific bank
python datasets/upload_to_ingestion.py 1
```

Uploads CSVs via HTTP to ingestion service, waits for Celery processing.

#### 4. Train Models

```bash
# Train for all banks
python datasets/train_models.py all

# Train for specific bank
python datasets/train_models.py 1
```

Trains:
- **Fraud Detection**: LightGBM classifier
- **Forecasting**: Prophet + NeuralProphet replacement

Models saved to:
- Local: `datasets/processed/bank_{id}/models/`
- S3/MinIO: `s3://{bucket}/models/fraud/bank_{id}/model.pkl`

### Option 3: Skip Steps

```bash
# Skip download (use existing datasets)
python datasets/run_e2e.py --skip-download

# Skip upload (datasets already ingested)
python datasets/run_e2e.py --skip-upload

# Skip training (models already trained)
python datasets/run_e2e.py --skip-training
```

## Validation

### Manual Validation

Check admin endpoint (requires admin JWT):
```bash
curl -H "Authorization: Bearer <admin_jwt>" \
     http://localhost:8000/admin/validate-datasets
```

### Expected Results

After full pipeline, you should see:

**Postgres** (per bank):
- Reports: 1 per uploaded file
- Transactions: ~50k-150k per bank
- Timeseries buckets: Daily aggregates

**Neo4j**:
- Transaction nodes: ~50k-150k per bank
- Merchant nodes: Varies
- Lifecycle edges: AUTHORIZED, CLEARED, SETTLED

**Pinecone**:
- Vector count: Embeddings for reports, transactions, summaries

## Model Artifacts

Trained models are stored in:
- **Local**: `datasets/processed/bank_{id}/models/`
- **S3/MinIO**: `s3://payscope-raw/models/`

Metrics saved to: `datasets/training_summary.json`

## Troubleshooting

### Kaggle API Errors

```bash
# Verify credentials
kaggle datasets list

# Or set environment variables
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_key
```

### Upload Failures

- Check ingestion service is running: `curl http://localhost:8080/health`
- Verify `X-Bank-Id` header is set correctly
- Check database connection: `DATABASE_URL` in `.env`

### Processing Timeout

- Increase wait time in `upload_to_ingestion.py` (`max_wait_minutes`)
- Check Celery worker logs: `docker compose logs worker`
- Verify all dependencies (Postgres, Neo4j, Pinecone) are accessible

### Model Training Errors

- Ensure LightGBM is installed: `pip install lightgbm`
- Check dataset has fraud column (for fraud model)
- Verify timestamp and amount columns exist (for forecasting)

## Dataset Sizes

After sampling, expected sizes:
- Bank 1 (CCFD): ~100k rows
- Bank 2 (IEEE-CIS): ~150k rows
- Bank 3 (PaySim): ~120k rows
- Bank 4 (Olist): ~100k rows
- Bank 5 (Synthetic): ~100k rows

**Total**: ~570k rows across all banks

## Next Steps

After running E2E pipeline:
1. ✅ Data loaded in Postgres, TimescaleDB, Neo4j, Pinecone
2. ✅ Models trained and saved
3. ✅ Ready for RAG queries
4. ✅ Ready for forecasting jobs
5. ✅ Monitor via Prometheus/Grafana

## Notes

- All sampling uses fixed seed (42) for reproducibility
- Class imbalance is preserved in fraud datasets
- Models are baseline (minimal hyperparameters) - production models would need tuning
- S3/MinIO uploads require credentials in `.env`

