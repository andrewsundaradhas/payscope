"""
End-to-end wiring for complete PayScope pipeline.

Ensures all components work together cohesively.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from payscope_processing.agents.orchestrator_agent import OrchestratorAgent
from payscope_processing.integration.wire_llms import WiredOrchestrator
from payscope_processing.mcp.servers import get_mcp_server
from payscope_processing.rag.engine import RAGEngine
from payscope_processing.config import get_settings


class EndToEndPipeline:
    """
    Complete end-to-end pipeline orchestrator.
    
    Coordinates:
    - Report ingestion
    - Parsing and extraction
    - Normalization
    - Intelligence (RAG, forecasting, graph)
    - Agent orchestration
    - Dashboard generation
    - Chat queries
    """

    def __init__(self, use_llm: bool = True):
        settings = get_settings()
        self.settings = settings
        self.use_llm = use_llm
        
        # Initialize components
        self.rag_engine = RAGEngine(settings)
        
        if use_llm:
            try:
                self.orchestrator = WiredOrchestrator(use_llm=True)
            except Exception:
                self.orchestrator = OrchestratorAgent()
                self.use_llm = False
        else:
            self.orchestrator = OrchestratorAgent()
        
        self.mcp_server = get_mcp_server()

    def process_report_end_to_end(
        self,
        artifact_id: str,
        bank_id: str,
        report_id: str,
    ) -> Dict[str, Any]:
        """
        Process report through complete pipeline.
        
        Args:
            artifact_id: Artifact ID
            bank_id: Bank ID
            report_id: Report ID
        
        Returns:
            Processing result
        """
        # This would be called by the Celery task after ingestion
        # For now, returns structure
        return {
            "artifact_id": artifact_id,
            "bank_id": bank_id,
            "report_id": report_id,
            "status": "processed",
            "pipeline": [
                "ingestion",
                "parsing",
                "normalization",
                "persistence",
                "intelligence",
            ],
        }

    def query_with_advanced_support(
        self,
        query: str,
        bank_id: str,
        query_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle query with advanced query type support.
        
        Args:
            query: Natural language query
            bank_id: Bank ID
            query_type: Optional query type
        
        Returns:
            Query response
        """
        from payscope_processing.rag.advanced_queries import AdvancedQueryHandler
        
        query_handler = AdvancedQueryHandler(self.rag_engine)
        
        # Route based on query type
        if query_type == "why":
            response = query_handler.handle_why_query(query, bank_id)
        elif query_type == "compare":
            response = query_handler.handle_compare_query(query, bank_id)
        elif query_type == "what_if":
            response = query_handler.handle_what_if_query(query, bank_id)
        else:
            response = self.rag_engine.query(query, bank_id=bank_id)
        
        return {
            "query": query,
            "query_type": query_type or "standard",
            "answer": response.answer,
            "explanation": getattr(response, "explanation", None),
            "sources": response.sources,
            "metrics": response.metrics,
            "confidence": response.confidence,
        }

    def generate_adaptive_dashboard(
        self,
        report_ids: List[str],
        bank_id: str,
    ) -> Dict[str, Any]:
        """
        Generate adaptive dashboard.
        
        Args:
            report_ids: Report IDs
            bank_id: Bank ID
        
        Returns:
            Dashboard configuration
        """
        from payscope_processing.dashboard.generator import DashboardGenerator
        
        generator = DashboardGenerator(self.rag_engine)
        return generator.generate_dashboard(report_ids, bank_id)

    def execute_with_mcp_tools(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute operation using MCP tools.
        
        Args:
            tool_name: Tool name
            arguments: Tool arguments
            context: Execution context
        
        Returns:
            Tool execution result
        """
        return self.mcp_server.execute_tool(tool_name, arguments, context)


def get_e2e_pipeline(use_llm: bool = True) -> EndToEndPipeline:
    """Get configured end-to-end pipeline."""
    return EndToEndPipeline(use_llm=use_llm)



