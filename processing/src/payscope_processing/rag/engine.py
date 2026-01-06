from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List

from payscope_processing.agents.orchestrator_agent import OrchestratorAgent
from payscope_processing.config import Settings
from payscope_processing.rag.intent import classify_intent
from payscope_processing.rag.retrieval import retrieve_context
from payscope_processing.rag.response_schema import RAGResponse
from payscope_processing.agents.memory import build_vector_memory, build_graph_context
from payscope_processing.vector.embedder import Embedder, EmbeddingConfig
from payscope_processing.rag.timeseries_client import TimeseriesClient, TimeseriesConfig


class RAGEngine:
    """
    End-to-end RAG + agent reasoning pipeline.
    """

    def __init__(self, settings: Settings, logger: logging.Logger | None = None):
        self.settings = settings
        self.logger = logger or logging.getLogger("RAGEngine")
        self.orchestrator = OrchestratorAgent(self.logger)

        # Shared memory components
        self.embedder = Embedder(EmbeddingConfig(model_name=settings.embedding_model_name, device=settings.embedding_device))
        self.vector_memory = build_vector_memory(
            cfg=self._pinecone_cfg()
        )
        self.graph_ctx = build_graph_context(
            cfg=self._neo4j_cfg()
        )
        self.timeseries_client = TimeseriesClient(TimeseriesConfig(dsn=settings.database_dsn))

    def run(self, query: str, filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        filters = filters or {}
        query_id = str(uuid.uuid4())
        bank_id = filters.get("bank_id", "unknown")

        # 1) Intent classification
        intent_res = classify_intent(self.settings, query)

        # 2) Retrieval
        ctx = retrieve_context(
            query=query,
            embedder=self.embedder,
            vector_memory=self.vector_memory,
            graph=self.graph_ctx,
            timeseries=self.timeseries_client,
            filters={
                "vector_filter": {
                    k: v for k, v in {
                        "report_id": filters.get("report_id"),
                        "lifecycle_stage": filters.get("lifecycle_stage"),
                        "bank_id": bank_id,
                    }.items() if v is not None
                },
                "source_network": filters.get("source_network"),
                "lifecycle_stage": filters.get("lifecycle_stage"),
            },
            top_k=filters.get("top_k", 8),
        )

        # 3) Agent invocation (subset based on intent)
        agents_used: List[str] = []
        orchestrator_input: Dict[str, Any] = {
            "task_id": query_id,
            "bank_id": bank_id,
            "ingestion_summary": filters.get("ingestion_summary", {}),
            "lifecycle_records": filters.get("lifecycle_records", []),
            "timeseries": ctx.get("timeseries", {}).get("transaction_volume", []),
            "scenario": filters.get("scenario", {}),
            "artifacts": {
                "canonical_records": filters.get("canonical_records", []),
                "vectors": ctx.get("vector_hits", []),
                "graph_nodes": ctx.get("graph_nodes", []),
            },
        }

        intent = intent_res.intent
        if intent == "FORECAST":
            agents_used = ["ForecastingAgent", "ComplianceAgent"]
        elif intent == "WHAT_IF_SIMULATION":
            agents_used = ["SimulationAgent", "ComplianceAgent"]
        elif intent == "COMPARISON":
            agents_used = ["ReconciliationAgent", "FraudAgent", "ComplianceAgent"]
        else:  # DESCRIPTIVE default
            agents_used = ["ReconciliationAgent", "FraudAgent", "ComplianceAgent"]

        # Let orchestrator run full graph; unused inputs are tolerated
        agent_output = self.orchestrator.invoke(orchestrator_input)

        # 4) Response synthesis (no hallucinated numbers: derive from retrieved context + agent outputs)
        numbers = {}
        forecast = agent_output.get("forecast", {}).get("forecast")
        if forecast:
            numbers.update(forecast)

        fraud = agent_output.get("fraud", {}).get("fraud_scores")
        if fraud:
            numbers["fraud_scores"] = fraud

        reconciliation = agent_output.get("reconciliation", {}).get("reconciled")
        if reconciliation:
            numbers["anomalies"] = reconciliation

        simulation = agent_output.get("simulation", {}).get("simulation")
        if simulation:
            numbers.update(simulation)

        explanation_parts = []
        if intent == "FORECAST" and forecast:
            explanation_parts.append("Forecast derived via EMA over retrieved time-series.")
        if fraud:
            explanation_parts.append("Fraud scores derived from lifecycle anomalies.")
        if reconciliation:
            explanation_parts.append("Lifecycle reconciliation checked for amount/currency/timestamp consistency.")
        if simulation:
            explanation_parts.append("What-if simulation uses deterministic stress multipliers.")

        explanation = " ".join(explanation_parts) or "Deterministic agent synthesis."

        # Confidence: blend intent confidence + compliance gate
        resp_conf = intent_res.confidence
        if agent_output.get("status") == "needs_review":
            resp_conf = min(resp_conf, 0.5)

        response = RAGResponse(
            explanation=explanation,
            numbers=numbers,
            confidence=resp_conf,
        ).model_dump()

        # 5) Mandatory query log
        log_payload = {
            "query_id": query_id,
            "intent": intent,
            "retrieval_sources": ["vector", "graph", "timeseries"],
            "agents_used": agents_used,
            "response_confidence": resp_conf,
            "bank_id": bank_id,
            "timestamp": response.get("timestamp", None) or None,
        }
        self.logger.info(json.dumps(log_payload, ensure_ascii=False))

        return response

    def query(self, query: str, bank_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        Query method compatible with advanced query handlers.
        
        Wraps run() method for consistent API.
        """
        filters = kwargs.copy()
        if bank_id:
            filters["bank_id"] = bank_id
        
        result = self.run(query, filters=filters)
        
        # Convert to StructuredResponse-like format
        from payscope_processing.rag.response_schema import RAGResponse
        
        # If result is already dict, return as-is but ensure StructuredResponse fields
        if isinstance(result, dict):
            # Extract fields to match StructuredResponse pattern
            return {
                "answer": result.get("explanation", ""),
                "explanation": result.get("explanation", ""),
                "sources": [],  # Sources should come from retrieval
                "metrics": result.get("numbers", {}),
                "confidence": result.get("confidence", 0.8),
                **result,
            }
        
        return result

    def _pinecone_cfg(self):
        from payscope_processing.vector.pinecone_client import PineconeConfig
        return PineconeConfig(
            api_key=self.settings.pinecone_api_key or "",
            index_name=self.settings.pinecone_index_name or "",
            namespace=self.settings.pinecone_namespace,
        )

    def _neo4j_cfg(self):
        from payscope_processing.graph.neo4j_writer import Neo4jConfig
        return Neo4jConfig(
            uri=self.settings.neo4j_uri or "",
            user=self.settings.neo4j_user or "",
            password=self.settings.neo4j_password or "",
        )


