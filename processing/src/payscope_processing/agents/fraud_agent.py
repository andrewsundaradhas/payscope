from __future__ import annotations

from typing import Any, Dict, List

from payscope_processing.agents.base import AgentBase, AgentLogRecord


class FraudAgent(AgentBase):
    """
    Analyzes anomalies and risk patterns; produces fraud risk scores.
    Stateless; uses rule-based scoring for determinism.
    """

    name = "FraudAgent"
    tools = ["graph_read", "vector_memory_read"]

    def run(self, task_id: str, *, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = []
        for a in anomalies:
            risk = 0.1
            if a.get("missing_settlement"):
                risk += 0.3
            if a.get("has_amount_mismatch"):
                risk += 0.25
            if a.get("currency_conflict"):
                risk += 0.15
            if a.get("timestamp_violation"):
                risk += 0.1
            gap = a.get("lifecycle_gap_duration")
            if gap and gap > 86400:  # >1 day gap
                risk += 0.1
            risk = min(1.0, risk)
            scores.append({"transaction_id": a.get("transaction_id"), "fraud_risk_score": risk})

        output = {"fraud_scores": scores}
        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"anomalies": anomalies},
                outputs=output,
                confidence=0.8,
                decision_rationale="deterministic rule-based risk scoring",
            )
        )
        return output




