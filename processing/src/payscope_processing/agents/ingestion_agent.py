from __future__ import annotations

from typing import Any, Dict

from payscope_processing.agents.base import AgentBase, AgentLogRecord


class IngestionAgent(AgentBase):
    """
    Validates ingestion completeness; detects missing/malformed reports.
    Stateless; no mutations of canonical facts.
    """

    name = "IngestionAgent"
    tools = ["vector_memory_read", "graph_read"]

    def run(self, task_id: str, *, ingestion_summary: Dict[str, Any]) -> Dict[str, Any]:
        missing = [r for r in ingestion_summary.get("expected_reports", []) if r not in ingestion_summary.get("received_reports", [])]
        malformed = ingestion_summary.get("malformed_reports", [])
        output = {
            "missing_reports": missing,
            "malformed_reports": malformed,
            "status": "ok" if not missing and not malformed else "issues_detected",
        }
        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"ingestion_summary": ingestion_summary},
                outputs=output,
                confidence=1.0,
                decision_rationale="deterministic checklist",
            )
        )
        return output




