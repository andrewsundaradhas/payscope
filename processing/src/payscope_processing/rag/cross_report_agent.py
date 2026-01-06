"""
Agent for cross-report reasoning and analysis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from payscope_processing.agents.base import AgentBase, AgentLogRecord
from payscope_processing.rag.engine import RAGEngine


class CrossReportAgent(AgentBase):
    """
    Agent for cross-report analysis and reasoning.
    
    Handles:
    - Cross-report comparisons
    - Trend analysis across multiple reports
    - Anomaly detection across reports
    - Temporal analysis
    """

    name = "CrossReportAgent"
    tools = ["vector_memory_read", "graph_read", "timeseries_read"]

    def __init__(self, rag_engine: RAGEngine, logger=None):
        super().__init__(logger)
        self.rag_engine = rag_engine

    def analyze_cross_report_trends(
        self,
        task_id: str,
        *,
        report_ids: List[str],
        metric: str,
        bank_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze trends across multiple reports.
        
        Args:
            task_id: Task ID
            report_ids: List of report IDs
            metric: Metric to analyze
            bank_id: Bank ID
        
        Returns:
            Analysis result
        """
        # Use RAG engine to retrieve data from multiple reports
        query = f"Trend analysis for {metric} across reports {', '.join(report_ids)}"
        
        try:
            response = self.rag_engine.query(query, bank_id=bank_id)
            
            output = {
                "report_ids": report_ids,
                "metric": metric,
                "trend": "detected",
                "analysis": response.answer,
                "confidence": response.confidence,
            }
        except Exception as e:
            self.logger.warning(f"Cross-report analysis failed: {e}")
            output = {
                "report_ids": report_ids,
                "metric": metric,
                "trend": "unknown",
                "error": str(e),
            }

        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"report_ids": report_ids, "metric": metric, "bank_id": bank_id},
                outputs=output,
                confidence=output.get("confidence", 0.7),
                decision_rationale="cross-report trend analysis",
            )
        )
        return output

    def compare_reports(
        self,
        task_id: str,
        *,
        report_ids: List[str],
        dimensions: List[str],
        bank_id: str,
    ) -> Dict[str, Any]:
        """
        Compare metrics across reports.
        
        Args:
            task_id: Task ID
            report_ids: Report IDs to compare
            dimensions: Comparison dimensions
            bank_id: Bank ID
        
        Returns:
            Comparison result
        """
        query = f"Compare reports {', '.join(report_ids)} across {', '.join(dimensions)}"
        
        try:
            response = self.rag_engine.query(query, bank_id=bank_id)
            
            output = {
                "report_ids": report_ids,
                "dimensions": dimensions,
                "comparison": response.answer,
                "metrics": response.metrics or {},
                "confidence": response.confidence,
            }
        except Exception as e:
            self.logger.warning(f"Report comparison failed: {e}")
            output = {
                "report_ids": report_ids,
                "dimensions": dimensions,
                "error": str(e),
            }

        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"report_ids": report_ids, "dimensions": dimensions, "bank_id": bank_id},
                outputs=output,
                confidence=output.get("confidence", 0.7),
                decision_rationale="cross-report comparison",
            )
        )
        return output

    def detect_cross_report_anomalies(
        self,
        task_id: str,
        *,
        report_ids: List[str],
        bank_id: str,
    ) -> Dict[str, Any]:
        """
        Detect anomalies across multiple reports.
        
        Args:
            task_id: Task ID
            report_ids: Report IDs
            bank_id: Bank ID
        
        Returns:
            Anomaly detection result
        """
        query = f"Detect anomalies across reports {', '.join(report_ids)}"
        
        try:
            response = self.rag_engine.query(query, bank_id=bank_id)
            
            output = {
                "report_ids": report_ids,
                "anomalies_detected": True,
                "analysis": response.answer,
                "confidence": response.confidence,
            }
        except Exception as e:
            self.logger.warning(f"Anomaly detection failed: {e}")
            output = {
                "report_ids": report_ids,
                "anomalies_detected": False,
                "error": str(e),
            }

        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"report_ids": report_ids, "bank_id": bank_id},
                outputs=output,
                confidence=output.get("confidence", 0.7),
                decision_rationale="cross-report anomaly detection",
            )
        )
        return output



