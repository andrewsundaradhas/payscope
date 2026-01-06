from __future__ import annotations

import logging
from typing import Any, Dict, List

from langchain_core.runnables import Runnable

from payscope_processing.agents.base import AgentLogRecord
from payscope_processing.agents.compliance_agent import ComplianceAgent
from payscope_processing.agents.fraud_agent import FraudAgent
from payscope_processing.agents.forecasting_agent import ForecastingAgent
from payscope_processing.agents.ingestion_agent import IngestionAgent
from payscope_processing.agents.reconciliation_agent import ReconciliationAgent
from payscope_processing.agents.simulation_agent import SimulationAgent


class OrchestratorAgent(Runnable):
    """
    Coordinates agent execution with an explicit dependency graph and conflict resolution.
    Stateless; emits consolidated structured JSON.
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("OrchestratorAgent")
        self.ingestion = IngestionAgent(self.logger)
        self.reconciliation = ReconciliationAgent(self.logger)
        self.fraud = FraudAgent(self.logger)
        self.forecasting = ForecastingAgent(self.logger)
        self.simulation = SimulationAgent(self.logger)
        self.compliance = ComplianceAgent(self.logger)

    def invoke(self, input: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        task_id = input.get("task_id", "task")
        bank_id = input.get("bank_id", "unknown")

        # 1) Ingestion validation
        ingest_out = self.ingestion.run(task_id, ingestion_summary=input.get("ingestion_summary", {}))

        # 2) Reconciliation (uses lifecycle records)
        recon_out = self.reconciliation.run(task_id, lifecycle_records=input.get("lifecycle_records", []))

        # 3) Fraud (uses reconciliation anomalies)
        anomalies_for_fraud = [
            {**a["anomalies"], "transaction_id": a.get("transaction_id")}
            for a in recon_out.get("reconciled", [])
        ]
        fraud_out = self.fraud.run(task_id, anomalies=anomalies_for_fraud)

        # 4) Forecasting (time-series)
        forecast_out = self.forecasting.run(task_id, timeseries=input.get("timeseries", []))

        # 5) Simulation (what-if)
        simulation_out = self.simulation.run(task_id, scenario=input.get("scenario", {}))

        # 6) Compliance (traceability checks)
        compliance_out = self.compliance.run(task_id, artifacts=input.get("artifacts", {}))

        # Conflict resolution (simple deterministic precedence):
        # If compliance flags issues, set overall status to "needs_review".
        status = "ok"
        rationale = []
        if ingest_out.get("status") != "ok":
            status = "needs_review"
            rationale.append("ingestion_issues")
        if compliance_out.get("status") != "ok":
            status = "needs_review"
            rationale.append("compliance_issues")

        consolidated = {
            "task_id": task_id,
            "status": status,
            "rationale": rationale,
            "ingestion": ingest_out,
            "reconciliation": recon_out,
            "fraud": fraud_out,
            "forecast": forecast_out,
            "simulation": simulation_out,
            "compliance": compliance_out,
        }

        # Log orchestrator decision
        self.logger.info(
            AgentLogRecord(
                agent_name="OrchestratorAgent",
                task_id=task_id,
                inputs={"bank_id": bank_id, **input},
                outputs=consolidated,
                confidence=0.8,
                decision_rationale="deterministic precedence (compliance/ingestion gate)",
            ).to_json()
        )
        return consolidated


