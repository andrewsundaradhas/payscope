from __future__ import annotations

from typing import Any, Dict, List

from payscope_processing.agents.base import AgentBase, AgentLogRecord
from payscope_processing.graph.reasoning import LifecycleStageInfo, analyze_lifecycle


class ReconciliationAgent(AgentBase):
    """
    Matches AUTH → CLEARING → SETTLEMENT lifecycles, flags mismatches/unresolved cases.
    Stateless; does not mutate canonical facts.
    """

    name = "ReconciliationAgent"
    tools = ["graph_read"]

    def run(self, task_id: str, *, lifecycle_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        # lifecycle_records: list of {transaction_id, stages: [{stage, amount, currency, timestamp_utc}]}
        results = []
        for rec in lifecycle_records:
            stages = [
                LifecycleStageInfo(
                    stage=s["stage"],
                    amount=float(s["amount"]),
                    currency=str(s["currency"]),
                    timestamp_utc=s["timestamp_utc"],
                )
                for s in rec.get("stages", [])
            ]
            anomalies = analyze_lifecycle(stages)
            results.append(
                {
                    "transaction_id": rec.get("transaction_id"),
                    "anomalies": {
                        "has_amount_mismatch": anomalies.has_amount_mismatch,
                        "missing_settlement": anomalies.missing_settlement,
                        "currency_conflict": anomalies.currency_conflict,
                        "timestamp_violation": anomalies.timestamp_violation,
                        "lifecycle_gap_duration": anomalies.lifecycle_gap_duration,
                    },
                }
            )

        output = {"reconciled": results}
        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"lifecycle_records": lifecycle_records},
                outputs=output,
                confidence=1.0,
                decision_rationale="rule-based lifecycle checks",
            )
        )
        return output




