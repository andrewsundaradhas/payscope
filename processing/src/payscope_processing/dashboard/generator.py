"""
AI-generated dashboard generator.

Creates dynamic, configurable dashboards that auto-adapt to report schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from payscope_processing.rag.engine import RAGEngine
from payscope_processing.rag.intent import classify_intent


class DashboardGenerator:
    """
    Generates dynamic dashboards from report data.
    
    Auto-adapts to new report schemas and generates appropriate visualizations.
    """

    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine

    def generate_dashboard(
        self,
        report_ids: List[str],
        bank_id: str,
        metrics: Optional[List[str]] = None,
        chart_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate dashboard configuration.
        
        Args:
            report_ids: List of report IDs to include
            bank_id: Bank ID filter
            metrics: Specific metrics to include (None = auto-detect)
            chart_types: Chart types to use (None = auto-select)
        
        Returns:
            Dashboard configuration
        """
        # Auto-detect available metrics if not specified
        if not metrics:
            metrics = self._detect_available_metrics(report_ids, bank_id)
        
        # Auto-select chart types if not specified
        if not chart_types:
            chart_types = self._select_chart_types(metrics)
        
        # Generate dashboard widgets
        widgets = []
        for metric in metrics:
            widget = self._generate_widget(metric, bank_id, chart_types)
            widgets.append(widget)
        
        return {
            "dashboard_id": f"dashboard_{bank_id}_{hash(tuple(report_ids))}",
            "bank_id": bank_id,
            "report_ids": report_ids,
            "widgets": widgets,
            "layout": self._generate_layout(widgets),
            "metadata": {
                "generated_at": "auto",
                "schema_adaptive": True,
            },
        }

    def _detect_available_metrics(
        self,
        report_ids: List[str],
        bank_id: str,
    ) -> List[str]:
        """Auto-detect available metrics from reports."""
        # Query RAG engine to discover metrics
        # For now, return common metrics
        return [
            "transaction_volume",
            "fraud_count",
            "dispute_rate",
            "average_amount",
            "approval_rate",
        ]

    def _select_chart_types(self, metrics: List[str]) -> List[str]:
        """Auto-select appropriate chart types for metrics."""
        chart_map = {
            "transaction_volume": "line",
            "fraud_count": "bar",
            "dispute_rate": "line",
            "average_amount": "area",
            "approval_rate": "gauge",
        }
        return [chart_map.get(m, "line") for m in metrics]

    def _generate_widget(
        self,
        metric: str,
        bank_id: str,
        chart_types: List[str],
    ) -> Dict[str, Any]:
        """Generate widget configuration for a metric."""
        chart_type = chart_types[0] if chart_types else "line"
        
        return {
            "id": f"widget_{metric}",
            "type": "chart",
            "metric": metric,
            "chart_type": chart_type,
            "config": {
                "bank_id": bank_id,
                "time_range": "30d",
                "aggregation": "daily",
            },
        }

    def _generate_layout(self, widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate dashboard layout."""
        # Simple grid layout (can be enhanced)
        return {
            "type": "grid",
            "columns": 2,
            "rows": (len(widgets) + 1) // 2,
            "widgets": [w["id"] for w in widgets],
        }

    def adapt_to_schema(
        self,
        schema_info: Dict[str, Any],
        bank_id: str,
    ) -> Dict[str, Any]:
        """
        Adapt dashboard to new report schema.
        
        Args:
            schema_info: Schema information (columns, types, etc.)
            bank_id: Bank ID
        
        Returns:
            Adapted dashboard configuration
        """
        # Extract metrics from schema
        metrics = []
        for col, col_type in schema_info.get("columns", {}).items():
            if col_type in ["numeric", "float", "int"]:
                if any(term in col.lower() for term in ["amount", "volume", "count", "rate", "fee"]):
                    metrics.append(col)
        
        # Generate dashboard with discovered metrics
        return self.generate_dashboard(
            report_ids=[],
            bank_id=bank_id,
            metrics=metrics,
        )


def generate_adaptive_dashboard(
    rag_engine: RAGEngine,
    bank_id: str,
    schema_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate adaptive dashboard that auto-detects schema.
    
    Args:
        rag_engine: RAG engine for data retrieval
        bank_id: Bank ID
        schema_info: Optional schema information
    
    Returns:
        Dashboard configuration
    """
    generator = DashboardGenerator(rag_engine)
    
    if schema_info:
        return generator.adapt_to_schema(schema_info, bank_id)
    else:
        return generator.generate_dashboard([], bank_id)



