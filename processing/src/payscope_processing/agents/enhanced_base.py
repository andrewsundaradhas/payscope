"""
Enhanced agent base with LLM integration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from payscope_processing.agents.base import AgentBase, AgentLogRecord
from payscope_processing.llm.langchain_integration import create_agent_llm


class EnhancedAgentBase(AgentBase):
    """
    Enhanced agent base with LLM support.
    
    Maintains compatibility with existing AgentBase while adding LLM capabilities.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        llm: Optional[BaseLanguageModel] = None,
        use_llm: bool = True,
    ) -> None:
        super().__init__(logger)
        self.use_llm = use_llm
        if use_llm:
            try:
                self.llm = llm or create_agent_llm(use_o1=True)
            except Exception as e:
                self.logger.warning(f"LLM initialization failed: {e}. Running without LLM.")
                self.llm = None
                self.use_llm = False
        else:
            self.llm = None

    def _llm_call(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any] = None,
    ) -> str:
        """
        Make LLM call with structured prompts.
        
        Returns:
            LLM response text
        """
        if not self.use_llm or not self.llm:
            return ""

        messages: List[BaseMessage] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            self.logger.warning(f"LLM call failed: {e}")
            return ""

    def run(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Run agent task (to be implemented by subclasses).
        
        Can use self._llm_call() for LLM-assisted reasoning.
        """
        raise NotImplementedError




