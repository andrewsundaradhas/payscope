#!/usr/bin/env python3
"""
Complete ML training pipeline for PayScope.

Includes:
- Fraud detection models (LightGBM)
- Forecasting models (Prophet, NeuralProphet replacement)
- Model evaluation and metrics
- S3/MinIO persistence
- Integration with existing processing modules
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import boto3
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)

# Add processing module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "processing" / "src"))

try:
    from payscope_processing.forecast.prophet_model import train_prophet_model
    from payscope_processing.forecast.neuralprophet_model import train_neuralprophet
    FORECAST_AVAILABLE = True
except ImportError:
    print("[WARNING] Forecasting modules not available", file=sys.stderr)
    FORECAST_AVAILABLE = False
    train_prophet_model = None
    train_neuralprophet = None

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("[ERROR] lightgbm not installed. Install with: pip install lightgbm", file=sys.stderr)
    LIGHTGBM_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    print("[WARNING] Prophet not installed. Install with: pip install prophet", file=sys.stderr)
    PROPHET_AVAILABLE = False


def load_bank_data(bank_id: int) -> pd.DataFrame:
    """Load processed dataset for a bank."""
    csv_file = Path(f"datasets/processed/bank_{bank_id}/bank_{bank_id}_processed.csv")
    if not csv_file.exists():
        raise FileNotFoundError(f"Bank {bank_id} dataset not found: {csv_file}")
    return pd.read_csv(csv_file)


def train_fraud_detection(df: pd.DataFrame, bank_id: int, output_dir: Path) -> Dict:
    """
    Train comprehensive fraud detection model using LightGBM.
    
    Returns detailed metrics and model artifacts.
    """
    if not LIGHTGBM_AVAILABLE:
        return {"status": "skipped", "reason": "lightgbm_not_available"}

    print(f"\n[Bank {bank_id}] Training fraud detection model...")

    # Find fraud column
    fraud_col = None
    for col in ["is_fraud", "Class", "isFraud", "isFlaggedFraud"]:
        if col in df.columns:
            fraud_col = col
            break

    if not fraud_col or df[fraud_col].sum() == 0:
        print(f"  [SKIP] No fraud column or no fraud cases found")
        return {"status": "skipped", "reason": "no_fraud_column"}

    # Prepare features
    exclude_cols = [
        fraud_col,
        "transaction_id",
        "report_id",
        "merchant_id",
        "timestamp",
        "date",
        "time",
    ]
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    numeric_features = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_features:
        print(f"  [SKIP] No numeric features available")
        return {"status": "skipped", "reason": "no_features"}

    X = df[numeric_features].fillna(0)
    # Handle NaN/inf values in fraud column
    y = df[fraud_col].fillna(0).replace([np.inf, -np.inf], 0).astype(int)

    # Train/test split (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"  Features: {len(numeric_features)}")
    print(f"  Training: {len(X_train):,} (fraud: {y_train.sum():,}, {y_train.mean()*100:.2f}%)")
    print(f"  Test: {len(X_test):,} (fraud: {y_test.sum():,}, {y_test.mean()*100:.2f}%)")

    # Train LightGBM with class weight handling for imbalanced data
    model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.1,
        random_state=42,
        verbose=-1,
        class_weight='balanced',  # Handle imbalanced data
        objective='binary',
        metric='binary_logloss',
    )
    
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)],
    )

    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    # Metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)
    accuracy = accuracy_score(y_test, y_pred)
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    
    # Classification report
    class_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    conf_matrix = confusion_matrix(y_test, y_pred).tolist()

    print(f"  AUC-ROC: {auc_score:.4f}")
    print(f"  AUC-PR: {pr_auc:.4f}")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Precision: {class_report['1'].get('precision', 0):.4f}")
    print(f"  Recall: {class_report['1'].get('recall', 0):.4f}")

    # Save model
    model_file = output_dir / f"fraud_model_bank_{bank_id}.pkl"
    joblib.dump(model, model_file)
    print(f"  Saved: {model_file}")

    # Save feature importance
    feature_importance = dict(zip(numeric_features, model.feature_importances_))
    importance_file = output_dir / f"fraud_features_bank_{bank_id}.json"
    importance_file.write_text(json.dumps(feature_importance, indent=2))

    # Upload to S3/MinIO
    s3_key = f"models/fraud/bank_{bank_id}/model.pkl"
    upload_to_s3(model_file, s3_key)

    return {
        "status": "success",
        "model_path": str(model_file),
        "s3_key": s3_key,
        "metrics": {
            "auc_roc": float(auc_score),
            "auc_pr": float(pr_auc),
            "accuracy": float(accuracy),
            "precision": class_report['1'].get('precision', 0),
            "recall": class_report['1'].get('recall', 0),
            "f1_score": class_report['1'].get('f1-score', 0),
            "n_features": len(numeric_features),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "confusion_matrix": conf_matrix,
        },
        "feature_importance": feature_importance,
    }


def train_forecasting_models(df: pd.DataFrame, bank_id: int, output_dir: Path) -> Dict:
    """
    Train comprehensive forecasting models (Prophet + NeuralProphet replacement).
    """
    print(f"\n[Bank {bank_id}] Training forecasting models...")

    if not FORECAST_AVAILABLE:
        return {"status": "skipped", "reason": "forecasting_modules_not_available"}

    # Find timestamp and amount columns
    time_col = None
    amount_col = None

    for col in df.columns:
        if "time" in col.lower() or "date" in col.lower() or "timestamp" in col.lower():
            if time_col is None:
                time_col = col
        if ("amount" in col.lower() or "value" in col.lower() or "transactionamt" in col.lower() or 
            "price" in col.lower() or "payment" in col.lower() or "total" in col.lower()):
            if amount_col is None:
                amount_col = col

    if not time_col or not amount_col:
        print(f"  [SKIP] Missing time or amount columns (time: {time_col}, amount: {amount_col})")
        return {"status": "skipped", "reason": "missing_columns"}

    # Prepare time-series data
    ts_df = df[[time_col, amount_col]].copy()
    ts_df[time_col] = pd.to_datetime(ts_df[time_col], errors="coerce")
    ts_df = ts_df.dropna()

    if len(ts_df) < 100:
        print(f"  [SKIP] Insufficient time-series data ({len(ts_df)} rows)")
        return {"status": "skipped", "reason": "insufficient_data"}

    # Aggregate by day
    ts_df["date"] = ts_df[time_col].dt.date
    daily = ts_df.groupby("date")[amount_col].sum().reset_index()
    daily.columns = ["ds", "y"]
    daily["ds"] = pd.to_datetime(daily["ds"])

    print(f"  Time series: {len(daily)} days")
    print(f"  Date range: {daily['ds'].min()} to {daily['ds'].max()}")
    print(f"  Total volume: {daily['y'].sum():,.2f}")

    results = {}

    # Train Prophet
    if PROPHET_AVAILABLE and train_prophet_model:
        try:
            print("  Training Prophet...")
            daily_prophet = daily.copy()
            daily_prophet["bucket_time"] = daily_prophet["ds"]
            prophet_result = train_prophet_model(
                feature_frame=daily_prophet,
                target_col="y",
                horizon_days=14,
                model_dir=str(output_dir / "prophet"),
            )
            results["prophet"] = {
                "status": "success",
                "model_path": prophet_result.get("artifact", {}).get("model_path", ""),
                "train_size": prophet_result.get("train_size", 0),
                "test_size": prophet_result.get("test_size", 0),
            }
            print(f"    [OK] Prophet trained (train: {prophet_result.get('train_size')}, test: {prophet_result.get('test_size')})")
        except Exception as e:
            print(f"    [FAIL] Prophet failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            results["prophet"] = {"status": "failed", "error": str(e)}

    # Train NeuralProphet replacement
    if train_neuralprophet:
        try:
            print("  Training NeuralProphet replacement...")
            daily_np = daily.copy()
            daily_np["bucket_time"] = daily_np["ds"]
            np_result = train_neuralprophet(
                feature_frame=daily_np,
                target_col="y",
                horizon_days=14,
                model_dir=str(output_dir / "neuralprophet"),
            )
            results["neuralprophet"] = {
                "status": "success",
                "model_path": np_result.get("artifact", {}).get("model_path", ""),
                "train_size": np_result.get("train_size", 0),
                "test_size": np_result.get("test_size", 0),
            }
            print(f"    [OK] NeuralProphet trained (train: {np_result.get('train_size')}, test: {np_result.get('test_size')})")
        except Exception as e:
            print(f"    [FAIL] NeuralProphet failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            results["neuralprophet"] = {"status": "failed", "error": str(e)}

    return results if results else {"status": "skipped", "reason": "no_models_available"}


def upload_to_s3(file_path: Path, s3_key: str) -> None:
    """Upload model file to S3/MinIO."""
    try:
        s3_endpoint = os.getenv("S3_ENDPOINT_URL")
        s3_access = os.getenv("S3_ACCESS_KEY_ID")
        s3_secret = os.getenv("S3_SECRET_ACCESS_KEY")
        
        if not all([s3_endpoint, s3_access, s3_secret]):
            print(f"  [WARNING] S3 credentials not configured, skipping upload", file=sys.stderr)
            return

        s3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access,
            aws_secret_access_key=s3_secret,
            region_name=os.getenv("S3_REGION", "us-east-1"),
        )
        bucket = os.getenv("S3_BUCKET", "payscope-raw")
        s3.upload_file(str(file_path), bucket, s3_key)
        print(f"  Uploaded to S3: s3://{bucket}/{s3_key}")
    except Exception as e:
        print(f"  [WARNING] S3 upload failed: {e}", file=sys.stderr)


def main():
    """Train complete ML pipeline for all banks."""
    if len(sys.argv) < 2:
        print("Usage: python train_ml_complete.py <bank_id>|all")
        sys.exit(1)

    bank_arg = sys.argv[1]
    bank_ids = [1, 2, 3, 4, 5] if bank_arg == "all" else [int(bank_arg)]

    print("=" * 60)
    print("PayScope Complete ML Training Pipeline")
    print("=" * 60)

    all_results = {}
    for bank_id in bank_ids:
        print(f"\n{'='*60}")
        print(f"Processing Bank {bank_id}")
        print(f"{'='*60}")
        
        try:
            df = load_bank_data(bank_id)
            output_dir = Path(f"datasets/processed/bank_{bank_id}/models")
            output_dir.mkdir(parents=True, exist_ok=True)

            bank_results = {}

            # Train fraud detection
            fraud_result = train_fraud_detection(df, bank_id, output_dir)
            bank_results["fraud"] = fraud_result

            # Train forecasting models
            forecast_result = train_forecasting_models(df, bank_id, output_dir)
            bank_results["forecasting"] = forecast_result

            all_results[bank_id] = bank_results

        except FileNotFoundError:
            print(f"\n[SKIP] Bank {bank_id}: Dataset not found")
            continue
        except Exception as e:
            print(f"\n[ERROR] Bank {bank_id} training failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue

    # Save comprehensive summary
    summary_file = Path("datasets/ml_training_summary.json")
    summary_file.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\n{'='*60}")
    print(f"[OK] Training complete! Summary saved: {summary_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

