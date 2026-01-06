from __future__ import annotations

from typing import Any, Dict, List

from payscope_processing.agents.base import AgentBase, AgentLogRecord


class ForecastingAgent(AgentBase):
    """
    Predicts volume, disputes, fraud trends using time-series + graph context.
    Deterministic baseline: simple moving averages/exponential smoothing coefficients.
    """

    name = "ForecastingAgent"
    tools = ["timeseries_read", "graph_read"]

    def run(self, task_id: str, *, timeseries: List[Dict[str, Any]]) -> Dict[str, Any]:
        # timeseries: list of {bucket_time, volume, disputes, fraud_count}
        def ema(series: List[float], alpha: float = 0.3) -> float:
            if not series:
                return 0.0
            v = series[0]
            for x in series[1:]:
                v = alpha * x + (1 - alpha) * v
            return v

        vols = [float(x.get("volume", 0)) for x in timeseries]
        disputes = [float(x.get("disputes", 0)) for x in timeseries]
        frauds = [float(x.get("fraud_count", 0)) for x in timeseries]

        forecast = {
            "volume_forecast": ema(vols),
            "dispute_forecast": ema(disputes),
            "fraud_forecast": ema(frauds),
        }

        output = {"forecast": forecast}
        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"timeseries": timeseries},
                outputs=output,
                confidence=0.7,
                decision_rationale="EMA smoothing (deterministic baseline)",
            )
        )
        return output




