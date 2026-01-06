from __future__ import annotations

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import pandas as pd
import numpy as np


@dataclass
class NeuralProphetArtifact:
    model_path: str
    version: str


def _fourier_features(dates: pd.Series, period: int, order: int = 3) -> pd.DataFrame:
    t = (dates.view("int64") // 10**9).values  # seconds
    feats = {}
    for k in range(1, order + 1):
        feats[f"sin_{period}_{k}"] = np.sin(2 * np.pi * k * t / (period * 86400))
        feats[f"cos_{period}_{k}"] = np.cos(2 * np.pi * k * t / (period * 86400))
    return pd.DataFrame(feats, index=dates.index)


def train_neuralprophet(
    *,
    feature_frame: pd.DataFrame,
    target_col: str,
    horizon_days: int = 14,
    model_dir: str = "./artifacts/neuralprophet",
) -> Dict[str, Any]:
    """
    NeuralProphet-like seasonal regression (Fourier features for weekly/monthly seasonality).
    Time-aware split; outputs forecast with intervals; persists artifact (weights + columns).
    """
    os.makedirs(model_dir, exist_ok=True)

    df = feature_frame.rename(columns={"bucket_time": "ds", target_col: "y"}).copy()
    df = df[["ds", "y"]].dropna()

    if len(df) < 20:
        raise ValueError("insufficient data for NeuralProphet-like model")

    df = df.sort_values("ds")
    cutoff = df["ds"].max() - pd.Timedelta(days=horizon_days)
    train = df[df["ds"] <= cutoff]
    test = df[df["ds"] > cutoff]

    # Design matrix with Fourier features (weekly=7, monthly=30)
    def design(mat):
        f_week = _fourier_features(mat["ds"], period=7, order=3)
        f_month = _fourier_features(mat["ds"], period=30, order=3)
        X = pd.concat([pd.Series(1.0, index=mat.index, name="bias"), f_week, f_month], axis=1)
        return X.values, mat["y"].values

    X_train, y_train = design(train)
    X_test, y_test = design(test)

    # Closed-form ridge regression for determinism
    reg = 1e-3
    XtX = X_train.T @ X_train + reg * np.eye(X_train.shape[1])
    Xty = X_train.T @ y_train
    w = np.linalg.solve(XtX, Xty)

    def predict(dates):
        tmp = pd.DataFrame({"ds": dates})
        X, _ = design(tmp.assign(y=0))
        yhat = X @ w
        return yhat, X

    # Forecast future horizon
    future_dates = pd.date_range(df["ds"].max() + pd.Timedelta(days=1), periods=horizon_days, freq="D", tz="UTC")
    train_pred, _ = predict(train["ds"])
    test_pred, _ = predict(test["ds"])
    future_pred, _ = predict(future_dates)

    # Residual std for intervals
    residuals = y_train - train_pred
    sigma = float(np.std(residuals)) if len(residuals) > 1 else 0.0

    def pack(dates, preds):
        return [
            {
                "ds": d.isoformat(),
                "yhat": float(preds[i]),
                "yhat_lower": float(preds[i] - 1.96 * sigma),
                "yhat_upper": float(preds[i] + 1.96 * sigma),
            }
            for i, d in enumerate(dates)
        ]

    fc_hist = pack(train["ds"], train_pred) + pack(test["ds"], test_pred)
    fc_future = pack(future_dates, future_pred)
    forecast = fc_hist + fc_future

    version = datetime.utcnow().isoformat()
    model_path = os.path.join(model_dir, f"neuralprophet_like_{target_col}_{uuid.uuid4().hex[:8]}.json")
    artifact_payload = {"weights": w.tolist(), "sigma": sigma, "target": target_col}
    with open(model_path, "w", encoding="utf-8") as f:
        json.dump(artifact_payload, f)

    return {
        "artifact": NeuralProphetArtifact(model_path=model_path, version=version),
        "forecast": forecast,
        "train_size": len(train),
        "test_size": len(test),
        "target": target_col,
    }


