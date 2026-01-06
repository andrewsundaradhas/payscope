from __future__ import annotations

from typing import Any, Dict

from payscope_processing.agents.base import AgentBase, AgentLogRecord


class SimulationAgent(AgentBase):
    """
    Runs what-if scenarios; stress-tests system conditions.
    Deterministic: uses simple stress multipliers (no mutation of facts).
    """

    name = "SimulationAgent"
    tools = ["graph_read", "timeseries_read"]

    def run(self, task_id: str, *, scenario: Dict[str, Any]) -> Dict[str, Any]:
        # scenario example: {"volume_multiplier": 1.5, "fraud_multiplier": 2.0}
        vm = float(scenario.get("volume_multiplier", 1.0))
        fm = float(scenario.get("fraud_multiplier", 1.0))
        stress = {
          "simulated_volume_delta_pct": (vm - 1.0) * 100.0,
          "simulated_fraud_delta_pct": (fm - 1.0) * 100.0,
        }
        output = {"simulation": stress}
        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"scenario": scenario},
                outputs=output,
                confidence=0.6,
                decision_rationale="deterministic stress multipliers",
            )
        )
        return output




