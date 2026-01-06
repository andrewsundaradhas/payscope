from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from prophet import Prophet


@dataclass
class ProphetModelArtifact:
    model_path: str
    version: str


def train_prophet_model(
    *,
    feature_frame: pd.DataFrame,
    target_col: str,
    horizon_days: int = 14,
    model_dir: str = "./artifacts/prophet",
) -> Dict[str, Any]:
    """
    Deterministic Prophet training with time-aware split.
    Outputs forecast with confidence intervals and persists model artifact.
    """
    os.makedirs(model_dir, exist_ok=True)

    df = feature_frame.rename(columns={"bucket_time": "ds", target_col: "y"}).copy()
    df = df[["ds", "y"]].dropna()

    if len(df) < 10:
        raise ValueError("insufficient data for Prophet")

    # Time-aware split: last horizon_days for test
    cutoff = df["ds"].max() - pd.Timedelta(days=horizon_days)
    train = df[df["ds"] <= cutoff]
    test = df[df["ds"] > cutoff]

    m = Prophet(interval_width=0.9, yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
    m.fit(train)

    future = m.make_future_dataframe(periods=horizon_days, freq="D", include_history=True)
    forecast = m.predict(future)

    version = datetime.utcnow().isoformat()
    model_path = os.path.join(model_dir, f"prophet_{target_col}_{uuid.uuid4().hex[:8]}.json")
    m.serialize(model_path)

    # Confidence intervals from forecast (yhat_lower/upper)
    merged = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].merge(df, on="ds", how="left", suffixes=("", "_actual"))

    return {
        "artifact": ProphetModelArtifact(model_path=model_path, version=version),
        "forecast": merged.to_dict(orient="records"),
        "train_size": len(train),
        "test_size": len(test),
        "target": target_col,
    }




