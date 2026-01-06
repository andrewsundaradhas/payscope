from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from payscope_processing.forecast.feature_engineering import build_features
from payscope_processing.forecast.prophet_model import train_prophet_model
from payscope_processing.forecast.neuralprophet_model import train_neuralprophet
from payscope_processing.forecast.gnn_risk import infer_risk, build_snapshot


def run_simulation(
    *,
    baseline_timeseries: Dict[str, Any],
    graph_nodes: list[dict],
    graph_edges: list[tuple[str, str]],
    scenario: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Runs baseline vs scenario forecasts + graph risk propagation.
    No mutation of inputs; scenario applied on cloned data.
    """
    run_id = str(uuid.uuid4())
    ts_base = copy.deepcopy(baseline_timeseries)
    ts_scn = apply_scenario(copy.deepcopy(baseline_timeseries), scenario)

    # Build features
    feat_base = build_features(ts_base)
    feat_scn = build_features(ts_scn)

    # Forecasts
    base_prophet = train_prophet_model(feature_frame=feat_base.df, target_col="transaction_volume")
    scn_prophet = train_prophet_model(feature_frame=feat_scn.df, target_col="transaction_volume")

    base_np = train_neuralprophet(feature_frame=feat_base.df, target_col="transaction_volume")
    scn_np = train_neuralprophet(feature_frame=feat_scn.df, target_col="transaction_volume")

    # Graph risk
    snapshot_base = build_snapshot(graph_nodes, graph_edges)
    snapshot_scn = build_snapshot(apply_risk_shift(graph_nodes, scenario), graph_edges)
    risk_base = infer_risk(snapshot_base)
    risk_scn = infer_risk(snapshot_scn)

    delta_metrics = {
        "prophet_delta": diff_forecasts(base_prophet["forecast"], scn_prophet["forecast"]),
        "neuralprophet_delta": diff_forecasts(base_np["forecast"], scn_np["forecast"]),
        "risk_shift": {k: risk_scn.get(k, 0) - risk_base.get(k, 0) for k in risk_scn},
    }

    log_payload = {
        "run_id": run_id,
        "model_type": "simulation",
        "scenario": scenario or {},
        "parameters": scenario or {},
        "confidence_intervals": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "run_id": run_id,
        "baseline": {
            "prophet": base_prophet,
            "neuralprophet": base_np,
            "risk": risk_base,
        },
        "scenario": {
            "prophet": scn_prophet,
            "neuralprophet": scn_np,
            "risk": risk_scn,
        },
        "delta_metrics": delta_metrics,
        "log": log_payload,
    }


def apply_scenario(ts: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    vol_mult = 1.0 + float(scenario.get("volume_spike", 0)) / 100.0
    fraud_mult = 1.0 + float(scenario.get("fraud_rate_increase", 0)) / 100.0
    # merchant_failure_rate not directly modeled; can be used to raise base risk later.

    for rec in ts.get("transaction_volume", []):
        if "tx_count" in rec:
            rec["tx_count"] = rec["tx_count"] * vol_mult
        if "amount_sum" in rec:
            rec["amount_sum"] = rec["amount_sum"] * vol_mult

    for rec in ts.get("fraud_counts", []):
        if "fraud_count" in rec:
            rec["fraud_count"] = rec["fraud_count"] * fraud_mult

    return ts


def apply_risk_shift(nodes: list[dict], scenario: Dict[str, Any]) -> list[dict]:
    fraud_mult = 1.0 + float(scenario.get("fraud_rate_increase", 0)) / 100.0
    merchant_fail = float(scenario.get("merchant_failure_rate", 0)) / 100.0
    out = []
    for n in nodes:
        nn = dict(n)
        base = float(nn.get("base_risk", 0.1))
        if nn.get("label") == "merchant":
            base *= fraud_mult
            base += merchant_fail
        nn["base_risk"] = min(1.0, base)
        out.append(nn)
    return out


def diff_forecasts(base: list[dict], scn: list[dict]) -> list[dict]:
    base_map = {r["ds"]: r for r in base if "ds" in r}
    deltas = []
    for r in scn:
        ds = r.get("ds")
        if ds in base_map:
            deltas.append(
                {
                    "ds": ds,
                    "yhat_delta": r.get("yhat", 0) - base_map[ds].get("yhat", 0),
                    "yhat_lower_delta": r.get("yhat_lower", 0) - base_map[ds].get("yhat_lower", 0),
                    "yhat_upper_delta": r.get("yhat_upper", 0) - base_map[ds].get("yhat_upper", 0),
                }
            )
    return deltas




