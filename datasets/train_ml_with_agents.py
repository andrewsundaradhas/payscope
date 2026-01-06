#!/usr/bin/env python3
"""
ML training pipeline with LLM agents (LLaMA 3.1 TGI + OpenAI o1 + CrewAI + LangChain).
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

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

# Add processing modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "processing" / "src"))

try:
    from payscope_processing.ml_agents.fraud_agent import FraudDetectionAgent
    from payscope_processing.ml_agents.forecast_agent import ForecastingAgent
    from payscope_processing.ml_agents.crew_setup import MLAgentCrew
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Agent modules not available: {e}", file=sys.stderr)
    AGENTS_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from payscope_processing.forecast.prophet_model import train_prophet_model
    from payscope_processing.forecast.neuralprophet_model import train_neuralprophet
    FORECAST_AVAILABLE = True
except ImportError:
    FORECAST_AVAILABLE = False
    train_prophet_model = None
    train_neuralprophet = None


def load_bank_data(bank_id: int) -> pd.DataFrame:
    """Load processed dataset for a bank."""
    csv_file = Path(f"datasets/processed/bank_{bank_id}/bank_{bank_id}_processed.csv")
    if not csv_file.exists():
        raise FileNotFoundError(f"Bank {bank_id} dataset not found: {csv_file}")
    return pd.read_csv(csv_file)


def train_fraud_with_agents(
    df: pd.DataFrame,
    bank_id: int,
    output_dir: Path,
    use_agents: bool = True,
) -> Dict:
    """
    Train fraud detection model with agent assistance.
    """
    if not LIGHTGBM_AVAILABLE:
        return {"status": "skipped", "reason": "lightgbm_not_available"}

    print(f"\n[Bank {bank_id}] Training fraud detection model with agents...")

    # Find fraud column
    fraud_col = None
    for col in ["is_fraud", "Class", "isFraud", "isFlaggedFraud"]:
        if col in df.columns:
            fraud_col = col
            break

    if not fraud_col or df[fraud_col].sum() == 0:
        print(f"  [SKIP] No fraud column or no fraud cases found")
        return {"status": "skipped", "reason": "no_fraud_column"}

    # Use agents to analyze and suggest features
    agent_recommendations = {}
    if use_agents and AGENTS_AVAILABLE:
        try:
            print("  [Agent] Analyzing data with CrewAI agents...")
            fraud_agent = FraudDetectionAgent()
            agent_recommendations = fraud_agent.analyze_fraud_data(df, fraud_col, bank_id)
            print("  [Agent] Analysis complete")
        except Exception as e:
            print(f"  [WARNING] Agent analysis failed: {e}", file=sys.stderr)
            use_agents = False

    # Get features (use agent suggestions if available)
    exclude_cols = [fraud_col, "transaction_id", "report_id", "merchant_id", "timestamp", "date", "time"]
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    numeric_features = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    if use_agents and AGENTS_AVAILABLE and agent_recommendations:
        # Use agent-suggested features if available
        suggested = fraud_agent.suggest_features(df, fraud_col)
        numeric_features = [f for f in suggested if f in numeric_features]

    if not numeric_features:
        return {"status": "skipped", "reason": "no_features"}

    X = df[numeric_features].fillna(0)
    y = df[fraud_col].fillna(0).replace([np.inf, -np.inf], 0).astype(int)

    # Train/test split
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"  Features: {len(numeric_features)}")
    print(f"  Training: {len(X_train):,} (fraud: {y_train.sum():,})")
    print(f"  Test: {len(X_test):,} (fraud: {y_test.sum():,})")

    # Train LightGBM
    model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.1,
        random_state=42,
        verbose=-1,
        class_weight='balanced',
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

    auc_score = roc_auc_score(y_test, y_pred_proba)
    accuracy = accuracy_score(y_test, y_pred)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    class_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    print(f"  AUC-ROC: {auc_score:.4f}")
    print(f"  AUC-PR: {pr_auc:.4f}")
    print(f"  Accuracy: {accuracy:.4f}")

    # Save model
    model_file = output_dir / f"fraud_model_bank_{bank_id}.pkl"
    joblib.dump(model, model_file)
    print(f"  Saved: {model_file}")

    return {
        "status": "success",
        "model_path": str(model_file),
        "metrics": {
            "auc_roc": float(auc_score),
            "auc_pr": float(pr_auc),
            "accuracy": float(accuracy),
            "precision": class_report['1'].get('precision', 0),
            "recall": class_report['1'].get('recall', 0),
        },
        "agent_recommendations": agent_recommendations if use_agents else None,
    }


def train_forecasting_with_agents(
    df: pd.DataFrame,
    bank_id: int,
    output_dir: Path,
    use_agents: bool = True,
) -> Dict:
    """
    Train forecasting models with agent assistance.
    """
    print(f"\n[Bank {bank_id}] Training forecasting models with agents...")

    if not FORECAST_AVAILABLE:
        return {"status": "skipped", "reason": "forecasting_modules_not_available"}

    # Find timestamp and amount columns
    time_col = None
    amount_col = None
    for col in df.columns:
        if "time" in col.lower() or "date" in col.lower() or "timestamp" in col.lower():
            if time_col is None:
                time_col = col
        if ("amount" in col.lower() or "value" in col.lower() or 
            "transactionamt" in col.lower() or "price" in col.lower() or
            "payment" in col.lower() or "total" in col.lower()):
            if amount_col is None:
                amount_col = col

    if not time_col or not amount_col:
        return {"status": "skipped", "reason": "missing_columns"}

    # Use agents to analyze time-series
    agent_recommendations = {}
    if use_agents and AGENTS_AVAILABLE:
        try:
            print("  [Agent] Analyzing time-series with CrewAI agents...")
            forecast_agent = ForecastingAgent()
            agent_recommendations = forecast_agent.analyze_time_series(
                df, time_col, amount_col, bank_id
            )
            print("  [Agent] Analysis complete")
        except Exception as e:
            print(f"  [WARNING] Agent analysis failed: {e}", file=sys.stderr)

    # Prepare time-series data
    ts_df = df[[time_col, amount_col]].copy()
    ts_df[time_col] = pd.to_datetime(ts_df[time_col], errors="coerce")
    ts_df = ts_df.dropna()

    if len(ts_df) < 100:
        return {"status": "skipped", "reason": "insufficient_data"}

    # Aggregate by day
    ts_df["date"] = ts_df[time_col].dt.date
    daily = ts_df.groupby("date")[amount_col].sum().reset_index()
    daily.columns = ["ds", "y"]
    daily["ds"] = pd.to_datetime(daily["ds"])

    print(f"  Time series: {len(daily)} days")

    results = {}

    # Train Prophet
    if train_prophet_model:
        try:
            daily_prophet = daily.copy()
            daily_prophet["bucket_time"] = daily_prophet["ds"]
            prophet_result = train_prophet_model(
                feature_frame=daily_prophet,
                target_col="y",
                horizon_days=14,
                model_dir=str(output_dir / "prophet"),
            )
            results["prophet"] = {"status": "success", "model_path": prophet_result.get("artifact", {}).get("model_path", "")}
        except Exception as e:
            results["prophet"] = {"status": "failed", "error": str(e)}

    # Train NeuralProphet
    if train_neuralprophet:
        try:
            daily_np = daily.copy()
            daily_np["bucket_time"] = daily_np["ds"]
            np_result = train_neuralprophet(
                feature_frame=daily_np,
                target_col="y",
                horizon_days=14,
                model_dir=str(output_dir / "neuralprophet"),
            )
            results["neuralprophet"] = {"status": "success", "model_path": np_result.get("artifact", {}).get("model_path", "")}
        except Exception as e:
            results["neuralprophet"] = {"status": "failed", "error": str(e)}

    return {
        **results,
        "agent_recommendations": agent_recommendations if use_agents else None,
    }


def main():
    """Train ML models with agent assistance."""
    if len(sys.argv) < 2:
        print("Usage: python train_ml_with_agents.py <bank_id>|all [--no-agents]")
        sys.exit(1)

    bank_arg = sys.argv[1]
    use_agents = "--no-agents" not in sys.argv
    bank_ids = [1, 2, 3, 4, 5] if bank_arg == "all" else [int(bank_arg)]

    print("=" * 60)
    print("PayScope ML Training with LLM Agents")
    print(f"Agents: {'Enabled' if use_agents else 'Disabled'}")
    print("=" * 60)

    if use_agents and not AGENTS_AVAILABLE:
        print("\n[WARNING] Agents requested but not available. Install:")
        print("  pip install crewai langchain langchain-openai")
        print("  Setting up TGI server for LLaMA 3.1 (optional)")
        use_agents = False

    all_results = {}
    for bank_id in bank_ids:
        try:
            df = load_bank_data(bank_id)
            output_dir = Path(f"datasets/processed/bank_{bank_id}/models")
            output_dir.mkdir(parents=True, exist_ok=True)

            bank_results = {}

            # Train fraud detection
            fraud_result = train_fraud_with_agents(df, bank_id, output_dir, use_agents)
            bank_results["fraud"] = fraud_result

            # Train forecasting
            forecast_result = train_forecasting_with_agents(df, bank_id, output_dir, use_agents)
            bank_results["forecasting"] = forecast_result

            all_results[bank_id] = bank_results

        except FileNotFoundError:
            print(f"\n[SKIP] Bank {bank_id}: Dataset not found")
            continue
        except Exception as e:
            print(f"\n[ERROR] Bank {bank_id} failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue

    # Save summary
    summary_file = Path("datasets/ml_training_with_agents_summary.json")
    summary_file.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\n[OK] Training complete! Summary: {summary_file}")


if __name__ == "__main__":
    main()



