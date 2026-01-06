# ML Training Pipeline - Complete Guide

## Overview

The ML training pipeline has been enhanced with comprehensive fraud detection and forecasting models that integrate with the existing PayScope processing infrastructure.

## Files

### 1. `train_ml_complete.py` (Enhanced - Recommended)
Complete ML training pipeline with:
- **Fraud Detection**: LightGBM with class balancing, comprehensive metrics
- **Forecasting**: Prophet + NeuralProphet replacement
- **Feature Importance**: Tracking and analysis
- **Metrics**: AUC-ROC, AUC-PR, Precision, Recall, F1, Confusion Matrix
- **S3 Persistence**: Automatic model upload to MinIO/S3

### 2. `train_models.py` (Basic)
Simplified version for quick training without advanced metrics.

## Features

### Fraud Detection Model

**Algorithm**: LightGBM Classifier
- Handles imbalanced datasets (fraud is typically rare)
- Early stopping to prevent overfitting
- Feature importance tracking
- Comprehensive evaluation metrics

**Metrics Collected**:
- AUC-ROC (Area Under ROC Curve)
- AUC-PR (Area Under Precision-Recall Curve)
- Accuracy
- Precision, Recall, F1-Score
- Confusion Matrix
- Feature Importance Rankings

### Forecasting Models

**Prophet**:
- Facebook's Prophet time-series forecasting
- Automatic seasonality detection
- Confidence intervals
- Handles missing data and outliers

**NeuralProphet Replacement**:
- Python 3.11 compatible alternative
- Fourier features for seasonality
- Ridge regression for determinism
- Uncertainty estimates

## Usage

### Train All Banks

```bash
python datasets/train_ml_complete.py all
```

### Train Specific Bank

```bash
python datasets/train_ml_complete.py 1
```

### Via E2E Pipeline

The E2E script automatically uses the enhanced training:

```bash
python datasets/run_e2e.py
```

## Dependencies

Install required packages:

```bash
pip install lightgbm scikit-learn prophet pandas numpy joblib boto3
```

## Outputs

### Models Saved Locally

```
datasets/processed/bank_{id}/models/
├── fraud_model_bank_{id}.pkl          # LightGBM fraud model
├── fraud_features_bank_{id}.json      # Feature importance
├── prophet/
│   └── prophet_{target}_{hash}.json   # Prophet model
└── neuralprophet/
    └── neuralprophet_{hash}.pkl       # NeuralProphet model
```

### Models Uploaded to S3/MinIO

- `s3://{bucket}/models/fraud/bank_{id}/model.pkl`
- Prophet and NeuralProphet models saved to local directory (can be uploaded separately)

### Training Summary

`datasets/ml_training_summary.json` contains:
- Training status per bank
- Metrics for each model
- Feature importance
- Model paths and S3 keys

## Integration with Existing Code

The training scripts integrate with existing PayScope modules:

- **Forecasting**: Uses `payscope_processing.forecast.prophet_model` and `neuralprophet_model`
- **S3 Storage**: Uses existing S3 configuration from `.env`
- **Data Format**: Compatible with normalized transaction data

## Model Performance

### Fraud Detection
- **Baseline**: AUC-ROC typically 0.85-0.95+ on fraud datasets
- **Class Balancing**: Automatically handles imbalanced fraud classes
- **Feature Selection**: Uses all numeric features from processed datasets

### Forecasting
- **Prophet**: Baseline forecasting with seasonality
- **NeuralProphet**: Advanced seasonality with Fourier features
- **Horizon**: 14-day forecasts by default

## Next Steps After Training

1. ✅ Models trained and saved
2. ✅ Models uploaded to S3 (if configured)
3. ✅ Metrics saved to summary JSON
4. → Models ready for inference via RAG engine
5. → Models can be loaded for real-time fraud detection
6. → Forecasting available via agent system

## Troubleshooting

### "lightgbm not installed"
```bash
pip install lightgbm
```

### "Prophet failed"
```bash
pip install prophet
```

### "Insufficient data"
- Ensure datasets are downloaded and processed
- Minimum 100 rows for forecasting
- At least some fraud cases for fraud detection

### "S3 upload failed"
- Check S3 credentials in `.env`
- Verify MinIO is running (if using local MinIO)
- Check bucket permissions

## Model Evaluation

After training, check `ml_training_summary.json` for:
- AUC-ROC scores (higher is better, >0.8 is good)
- Precision/Recall (fraud detection)
- Training/test split sizes
- Feature importance rankings

## Production Deployment

Models trained by this script are production-ready:
- Deterministic training (fixed random seeds)
- Idempotent (safe to re-run)
- Versioned artifacts
- Comprehensive logging

Load models in production:

```python
import joblib

# Load fraud model
model = joblib.load("datasets/processed/bank_1/models/fraud_model_bank_1.pkl")
predictions = model.predict_proba(features)
```



