#!/usr/bin/env python3
"""
Train baseline models for fraud detection and forecasting.

- Fraud: LightGBM (fast, minimal hyperparameters)
- Forecasting: Prophet + NeuralProphet replacement
- Models saved to S3/MinIO
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
from sklearn.metrics import auc, precision_recall_curve, roc_auc_score

# Import existing forecasting utilities
sys.path.insert(0, str(Path(__file__).parent.parent / "processing" / "src"))
try:
    from payscope_processing.forecast.prophet_model import train_prophet_model
    from payscope_processing.forecast.neuralprophet_model import train_neuralprophet
except ImportError:
    print("[WARNING] Forecasting modules not available", file=sys.stderr)
    train_prophet_model = None
    train_neuralprophet = None

try:
    import lightgbm as lgb
except ImportError:
    print("[ERROR] lightgbm not installed. Install with: pip install lightgbm", file=sys.stderr)
    sys.exit(1)


def load_bank_transactions(bank_id: int) -> pd.DataFrame:
    """Load transactions from processed dataset."""
    csv_file = Path(f"datasets/processed/bank_{bank_id}/bank_{bank_id}_processed.csv")
    if not csv_file.exists():
        raise FileNotFoundError(f"Bank {bank_id} dataset not found: {csv_file}")
    return pd.read_csv(csv_file)


def train_fraud_model(df: pd.DataFrame, bank_id: int, output_dir: Path) -> Dict:
    """
    Train LightGBM fraud detection model.

    Returns metrics and model path.
    """
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

    # Prepare features (exclude IDs and targets)
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

    # Remove non-numeric columns for simplicity
    numeric_features = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_features:
        print(f"  [SKIP] No numeric features available")
        return {"status": "skipped", "reason": "no_features"}

    X = df[numeric_features].fillna(0)
    y = df[fraud_col].astype(int)

    # Train/test split (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"  Features: {len(numeric_features)}")
    print(f"  Training samples: {len(X_train):,} (fraud: {y_train.sum():,})")
    print(f"  Test samples: {len(X_test):,} (fraud: {y_test.sum():,})")

    # Train LightGBM (minimal config)
    model = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.1,
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    auc_score = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)

    print(f"  AUC-ROC: {auc_score:.4f}")
    print(f"  AUC-PR: {pr_auc:.4f}")

    # Save model
    model_file = output_dir / f"fraud_model_bank_{bank_id}.pkl"
    joblib.dump(model, model_file)
    print(f"  Saved: {model_file}")

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
            "n_features": len(numeric_features),
            "n_train": len(X_train),
            "n_test": len(X_test),
        },
    }


def train_forecasting_model(df: pd.DataFrame, bank_id: int, output_dir: Path) -> Dict:
    """
    Train Prophet and NeuralProphet replacement for forecasting.

    Requires time-series data with timestamp and amount columns.
    """
    print(f"\n[Bank {bank_id}] Training forecasting models...")

    # Find timestamp and amount columns
    time_col = None
    amount_col = None

    for col in df.columns:
        if "time" in col.lower() or "date" in col.lower() or "timestamp" in col.lower():
            time_col = col
        if "amount" in col.lower() or "value" in col.lower():
            amount_col = col

    if not time_col or not amount_col:
        print(f"  [SKIP] Missing time or amount columns")
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
    daily.columns = ["ds", "y"]  # Prophet format

    print(f"  Time series: {len(daily)} days")

    results = {}

    # Train Prophet
    if train_prophet_model:
        try:
            print("  Training Prophet...")
            # Convert to proper format for Prophet (needs bucket_time column)
            daily_prophet = daily.copy()
            daily_prophet["bucket_time"] = pd.to_datetime(daily_prophet["ds"])
            prophet_result = train_prophet_model(
                feature_frame=daily_prophet,
                target_col="y",
                horizon_days=14,
                model_dir=str(output_dir / "prophet"),
            )
            results["prophet"] = {
                "status": "success",
                "model_dir": prophet_result.get("artifact", {}).get("model_path", ""),
                "train_size": prophet_result.get("train_size", 0),
                "test_size": prophet_result.get("test_size", 0),
            }
            print("    [OK] Prophet trained")
        except Exception as e:
            print(f"    [FAIL] Prophet failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            results["prophet"] = {"status": "failed", "error": str(e)}

    # Train NeuralProphet replacement
    if train_neuralprophet:
        try:
            print("  Training NeuralProphet replacement...")
            # Convert to proper format
            daily_np = daily.copy()
            daily_np["bucket_time"] = pd.to_datetime(daily_np["ds"])
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
            print("    [OK] NeuralProphet trained")
        except Exception as e:
            print(f"    [FAIL] NeuralProphet failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            results["neuralprophet"] = {"status": "failed", "error": str(e)}

    return results if results else {"status": "skipped", "reason": "no_models_available"}


def upload_to_s3(file_path: Path, s3_key: str) -> None:
    """Upload model file to S3/MinIO."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
            region_name=os.getenv("S3_REGION", "us-east-1"),
        )
        bucket = os.getenv("S3_BUCKET", "payscope-raw")
        s3.upload_file(str(file_path), bucket, s3_key)
        print(f"  Uploaded to S3: s3://{bucket}/{s3_key}")
    except Exception as e:
        print(f"  [WARNING] S3 upload failed: {e}", file=sys.stderr)


def main():
    """Train models for all banks."""
    if len(sys.argv) < 2:
        print("Usage: python train_models.py <bank_id> [all]")
        sys.exit(1)

    bank_ids = [int(sys.argv[1])] if sys.argv[1] != "all" else [1, 2, 3, 4, 5]

    print("=" * 60)
    print("Training Baseline Models")
    print("=" * 60)

    all_results = {}
    for bank_id in bank_ids:
        try:
            df = load_bank_transactions(bank_id)
            output_dir = Path(f"datasets/processed/bank_{bank_id}/models")
            output_dir.mkdir(parents=True, exist_ok=True)

            bank_results = {}

            # Train fraud model
            fraud_result = train_fraud_model(df, bank_id, output_dir)
            bank_results["fraud"] = fraud_result

            # Train forecasting models
            forecast_result = train_forecasting_model(df, bank_id, output_dir)
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

    # Save summary
    summary_file = Path("datasets/training_summary.json")
    summary_file.write_text(json.dumps(all_results, indent=2))
    print(f"\n[OK] Training summary: {summary_file}")


if __name__ == "__main__":
    main()

