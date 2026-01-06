from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd


@dataclass(frozen=True)
class FeatureFrame:
    df: pd.DataFrame
    version: str


def build_features(raw_ts: Dict[str, Any]) -> FeatureFrame:
    """
    Build deterministic time-series feature frame.
    raw_ts: {
      "transaction_volume": [{bucket_time, tx_count, amount_sum, ...}],
      "fraud_counts": [{bucket_time, fraud_count, ...}],
      "dispute_rates": [{bucket_time, dispute_rate, ...}],
      "avg_risk_scores": optional list,
      ...
    }
    """
    # Normalize time column
    def to_frame(records, time_col="bucket_time"):
        if not records:
            return pd.DataFrame(columns=[time_col])
        df = pd.DataFrame(records)
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        return df

    vol = to_frame(raw_ts.get("transaction_volume", []))
    fraud = to_frame(raw_ts.get("fraud_counts", []))
    disp = to_frame(raw_ts.get("dispute_rates", []))
    risk = to_frame(raw_ts.get("avg_risk_scores", []))

    # Merge on bucket_time
    df = vol.rename(columns={"tx_count": "transaction_volume"}).copy()
    for other in [
        fraud.rename(columns={"fraud_count": "fraud_count"}),
        disp.rename(columns={"dispute_rate": "dispute_rate"}),
        risk.rename(columns={"score": "average_risk_score"}),
    ]:
        if not other.empty:
            df = df.merge(other, on="bucket_time", how="outer")

    df = df.sort_values("bucket_time").reset_index(drop=True)

    # Fill NaNs deterministically (forward fill then zeros)
    df = df.ffill().bfill().fillna(0)

    # Derived features
    if "fraud_count" in df and "transaction_volume" in df:
        df["fraud_rate"] = df["fraud_count"] / df["transaction_volume"].replace(0, 1)
    if "dispute_rate" in df and "transaction_volume" in df:
        df["dispute_count_est"] = df["dispute_rate"] * df["transaction_volume"]
    # lifecycle_gap_duration optional
    if "lifecycle_gap_duration" not in df:
        df["lifecycle_gap_duration"] = 0
    if "average_risk_score" not in df:
        df["average_risk_score"] = 0
    df["merchant_behavior_score"] = df["average_risk_score"]  # placeholder derived alignment

    # Version hash
    sig = hashlib.sha256(json.dumps(sorted(df.columns.tolist())).encode()).hexdigest()[:8]
    return FeatureFrame(df=df, version=sig)




