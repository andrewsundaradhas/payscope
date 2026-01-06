from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentLogRecord:
    agent_name: str
    task_id: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    decision_rationale: str
    timestamp: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(
            {
                "agent_name": self.agent_name,
                "task_id": self.task_id,
                "inputs": self.inputs,
                "outputs": self.outputs,
                "confidence": self.confidence,
                "decision_rationale": self.decision_rationale,
                "timestamp": self.timestamp,
            },
            ensure_ascii=False,
        )


class AgentBase:
    """
    Base agent with deterministic, stateless behavior and structured logging.
    """

    name: str = "base"
    tools: List[str] = []

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.name)

    def log_action(self, record: AgentLogRecord) -> None:
        # Structured JSON log
        self.logger.info(record.to_json())

    def run(self, task_id: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError




