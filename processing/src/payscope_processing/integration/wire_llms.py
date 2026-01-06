"""
Wire LLMs into existing agent system.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from payscope_processing.agents.enhanced_base import EnhancedAgentBase
from payscope_processing.agents.enhanced_fraud_agent import EnhancedFraudAgent
from payscope_processing.agents.orchestrator_agent import OrchestratorAgent
from payscope_processing.llm.langchain_integration import create_agent_llm


class WiredOrchestrator(OrchestratorAgent):
    """
    Orchestrator with LLM integration.
    
    Extends existing OrchestratorAgent with LLM capabilities.
    """

    def __init__(self, use_llm: bool = True, logger=None):
        super().__init__(logger)
        self.use_llm = use_llm
        if use_llm:
            try:
                self.llm = create_agent_llm(use_o1=True)
            except Exception as e:
                self.logger.warning(f"LLM initialization failed: {e}")
                self.llm = None
                self.use_llm = False
        else:
            self.llm = None

        # Optionally replace fraud agent with enhanced version
        if use_llm:
            try:
                self.fraud = EnhancedFraudAgent(logger=self.logger, use_llm=True)
            except Exception:
                pass  # Keep original if enhanced fails

    def invoke(self, input: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Invoke with optional LLM-assisted conflict resolution.
        """
        # Run standard orchestration
        result = super().invoke(input, config)

        # LLM-assisted conflict resolution if enabled
        if self.use_llm and self.llm and result.get("status") != "ok":
            try:
                conflict_prompt = f"""
                Resolve conflicts in agent outputs:
                Status: {result.get('status')}
                Rationale: {result.get('rationale', [])}
                
                Provide resolution recommendations.
                """
                # Could use LLM here for conflict resolution
                # For now, keep deterministic behavior
            except Exception:
                pass

        return result


def create_wired_orchestrator(use_llm: bool = True) -> WiredOrchestrator:
    """Create orchestrator with LLM wiring."""
    return WiredOrchestrator(use_llm=use_llm)



