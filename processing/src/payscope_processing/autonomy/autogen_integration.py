"""
AutoGen integration for autonomous agent communication and task delegation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

try:
    import autogen
    from autogen import Agent, ConversableAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

from payscope_processing.agents.orchestrator_agent import OrchestratorAgent
from payscope_processing.llm.langchain_integration import create_agent_llm


class AutoGenOrchestrator:
    """
    AutoGen-based orchestrator for autonomous task execution.
    
    Wraps existing PayScope agents in AutoGen agents for autonomous collaboration.
    """

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        max_iter: int = 10,
        logger: Optional[logging.Logger] = None,
    ):
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen not installed. Install: pip install pyautogen")
        
        self.logger = logger or logging.getLogger("AutoGenOrchestrator")
        self.max_iter = max_iter
        
        # LLM config for AutoGen
        self.llm_config = llm_config or self._default_llm_config()
        
        # Create AutoGen agents
        self.agents = self._create_agents()
        self.group_chat = None
        self.manager = None

    def _default_llm_config(self) -> Dict[str, Any]:
        """Default LLM configuration."""
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return {
                "model": "gpt-4",
                "api_key": openai_key,
                "temperature": 0.7,
            }
        # Fallback: use local model if available
        return {
            "model": "gpt-3.5-turbo",
            "api_key": openai_key or "placeholder",
        }

    def _create_agents(self) -> Dict[str, ConversableAgent]:
        """Create AutoGen agents for each PayScope agent role."""
        agents = {}

        # Ingestion Agent
        agents["ingestion"] = ConversableAgent(
            name="ingestion_agent",
            system_message="You are an ingestion validation agent. You validate and process incoming data.",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.max_iter,
        )

        # Fraud Detection Agent
        agents["fraud"] = ConversableAgent(
            name="fraud_agent",
            system_message="You are a fraud detection agent. You analyze anomalies and compute fraud risk scores.",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.max_iter,
        )

        # Forecasting Agent
        agents["forecasting"] = ConversableAgent(
            name="forecasting_agent",
            system_message="You are a forecasting agent. You predict trends and volumes using time-series analysis.",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.max_iter,
        )

        # Compliance Agent
        agents["compliance"] = ConversableAgent(
            name="compliance_agent",
            system_message="You are a compliance agent. You ensure auditability and regulatory consistency.",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.max_iter,
        )

        # Orchestrator (manager)
        agents["orchestrator"] = ConversableAgent(
            name="orchestrator",
            system_message="You are the orchestrator. You coordinate tasks between agents and resolve conflicts.",
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=self.max_iter,
        )

        return agents

    def create_group_chat(self, agent_names: List[str]) -> GroupChat:
        """Create group chat with specified agents."""
        agents = [self.agents[name] for name in agent_names if name in self.agents]
        return GroupChat(agents=agents, messages=[], max_round=self.max_iter * len(agents))

    def execute_autonomous_task(
        self,
        task: str,
        agent_chain: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute task autonomously using AutoGen agents.
        
        Args:
            task: Task description
            agent_chain: List of agent names to involve (default: all)
        
        Returns:
            Execution results
        """
        if agent_chain is None:
            agent_chain = ["ingestion", "fraud", "forecasting", "compliance"]

        # Create group chat
        self.group_chat = self.create_group_chat(agent_chain)
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config,
        )

        # Initiate conversation
        orchestrator = self.agents["orchestrator"]
        result = orchestrator.initiate_chat(
            self.manager,
            message=task,
            max_turns=self.max_iter,
        )

        return {
            "task": task,
            "agents_involved": agent_chain,
            "result": result.summary if hasattr(result, "summary") else str(result),
            "messages": [str(m) for m in self.group_chat.messages],
        }


def get_autogen_orchestrator(
    llm_config: Optional[Dict[str, Any]] = None,
) -> Optional[AutoGenOrchestrator]:
    """Get AutoGen orchestrator if available."""
    if AUTOGEN_AVAILABLE:
        return AutoGenOrchestrator(llm_config=llm_config)
    return None

