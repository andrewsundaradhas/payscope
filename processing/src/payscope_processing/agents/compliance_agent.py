from __future__ import annotations

from typing import Any, Dict

from payscope_processing.agents.base import AgentBase, AgentLogRecord


class ComplianceAgent(AgentBase):
    """
    Ensures auditability and regulatory consistency; verifies traceability of outputs.
    Deterministic: checks presence of required trace fields.
    """

    name = "ComplianceAgent"
    tools = ["graph_read", "vector_memory_read"]

    def run(self, task_id: str, *, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        # artifacts: {"canonical_records": [...], "vectors": [...], "graph_nodes": [...]}
        missing_trace = []
        for rec in artifacts.get("canonical_records", []):
            if not rec.get("raw_source_ref"):
                missing_trace.append(rec.get("id"))
        for vec in artifacts.get("vectors", []):
            meta = vec.get("metadata", {})
            if not meta.get("report_id") or not meta.get("source_type"):
                missing_trace.append(vec.get("id"))
        for node in artifacts.get("graph_nodes", []):
            if not node.get("transaction_pk"):
                missing_trace.append(node.get("id"))

        output = {"traceability_issues": missing_trace, "status": "ok" if not missing_trace else "issues_detected"}
        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"artifacts": artifacts},
                outputs=output,
                confidence=1.0,
                decision_rationale="deterministic presence checks",
            )
        )
        return output




