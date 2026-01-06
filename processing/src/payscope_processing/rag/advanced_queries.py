"""
Advanced query handlers for why/compare/what-if queries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from payscope_processing.rag.engine import RAGEngine
from payscope_processing.rag.intent import IntentResult, classify_intent

# Intent types (string-based)
class IntentType:
    DESCRIPTIVE = "DESCRIPTIVE"
    COMPARISON = "COMPARISON"
    FORECAST = "FORECAST"
    WHAT_IF_SIMULATION = "WHAT_IF_SIMULATION"
# Use dict-based response structure (compatible with RAGResponse)
from typing import Any, Dict, List, Optional

# Response structure (dict-based for compatibility)
class StructuredResponse:
    """Response structure for advanced queries."""
    def __init__(
        self,
        intent: Any,
        answer: str,
        explanation: Optional[str] = None,
        sources: Optional[List[Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        confidence: float = 0.8,
    ):
        self.intent = intent
        self.answer = answer
        self.explanation = explanation
        self.sources = sources or []
        self.metrics = metrics or {}
        self.confidence = confidence


class AdvancedQueryHandler:
    """
    Handles advanced query types: why, compare, what-if.
    
    Integrates with RAG engine and agent system for complex reasoning.
    """

    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine

    def handle_why_query(
        self,
        query: str,
        bank_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> StructuredResponse:
        """
        Handle "why" queries - explain reasons behind metrics or trends.
        
        Args:
            query: Natural language query (e.g., "Why did fraud increase?")
            bank_id: Bank ID filter
            context: Additional context
        
        Returns:
            Structured response with explanation
        """
        # Enhanced intent classification
        intent = classify_intent(self.rag_engine._settings, query)
        
        # Add "why" intent if detected
        if "why" in query.lower() or "reason" in query.lower() or "explain" in query.lower():
            # Use RAG to retrieve relevant context
            response = self.rag_engine.query(query, bank_id=bank_id)
            
            # Enhance with explanation
            explanation = self._generate_explanation(query, response, bank_id)
            
            return StructuredResponse(
                intent=IntentType.DESCRIPTIVE,
                answer=response.answer,
                explanation=explanation,
                sources=response.sources,
                metrics=response.metrics,
                confidence=response.confidence,
            )
        
        # Fallback to standard RAG
        return self.rag_engine.query(query, bank_id=bank_id)

    def handle_compare_query(
        self,
        query: str,
        bank_id: str,
        dimensions: Optional[List[str]] = None,
    ) -> StructuredResponse:
        """
        Handle "compare" queries - compare metrics across dimensions.
        
        Args:
            query: Comparison query (e.g., "Compare fraud rates across banks")
            bank_id: Bank ID filter
            dimensions: Comparison dimensions
        
        Returns:
            Structured response with comparison
        """
        # Parse comparison query
        intent = classify_intent(self.rag_engine._settings, query)
        
        if hasattr(intent, "intent") and (intent.intent == IntentType.COMPARISON or "compare" in query.lower()):
            # Extract comparison dimensions
            if not dimensions:
                dimensions = self._extract_comparison_dimensions(query)
            
            # Execute comparison
            comparison_result = self._execute_comparison(
                query,
                dimensions,
                bank_id,
            )
            
            return StructuredResponse(
                intent=IntentType.COMPARISON,
                answer=comparison_result.get("summary", ""),
                explanation=comparison_result.get("explanation"),
                sources=comparison_result.get("sources", []),
                metrics=comparison_result.get("metrics", {}),
                confidence=comparison_result.get("confidence", 0.8),
            )
        
        # Fallback
        return self.rag_engine.query(query, bank_id=bank_id)

    def handle_what_if_query(
        self,
        query: str,
        bank_id: str,
        scenario: Optional[Dict[str, Any]] = None,
    ) -> StructuredResponse:
        """
        Handle "what-if" queries - scenario simulation.
        
        Args:
            query: What-if query (e.g., "What if we increase fees by 10%?")
            bank_id: Bank ID filter
            scenario: Scenario parameters
        
        Returns:
            Structured response with simulation results
        """
        intent = classify_intent(self.rag_engine._settings, query)
        
        if hasattr(intent, "intent") and (intent.intent == IntentType.WHAT_IF_SIMULATION or "what if" in query.lower()):
            # Extract scenario parameters
            if not scenario:
                scenario = self._extract_scenario_parameters(query)
            
            # Run simulation
            simulation_result = self._execute_simulation(
                query,
                scenario,
                bank_id,
            )
            
            return StructuredResponse(
                intent=IntentType.WHAT_IF_SIMULATION,
                answer=simulation_result.get("summary", ""),
                explanation=simulation_result.get("explanation"),
                sources=simulation_result.get("sources", []),
                metrics=simulation_result.get("metrics", {}),
                confidence=simulation_result.get("confidence", 0.75),
            )
        
        # Fallback
        return self.rag_engine.query(query, bank_id=bank_id)

    def _generate_explanation(
        self,
        query: str,
        response: StructuredResponse,
        bank_id: str,
    ) -> str:
        """Generate explanation for why query."""
        # Use agent system or LLM to generate explanation
        # For now, return enhanced answer
        return f"Explanation: {response.answer}\n\nBased on: {len(response.sources)} sources"

    def _extract_comparison_dimensions(self, query: str) -> List[str]:
        """Extract comparison dimensions from query."""
        # Simple extraction (can be enhanced with LLM)
        dimensions = []
        if "bank" in query.lower() or "banks" in query.lower():
            dimensions.append("bank_id")
        if "time" in query.lower() or "period" in query.lower():
            dimensions.append("time")
        if "merchant" in query.lower():
            dimensions.append("merchant_id")
        return dimensions or ["bank_id"]

    def _execute_comparison(
        self,
        query: str,
        dimensions: List[str],
        bank_id: str,
    ) -> Dict[str, Any]:
        """Execute comparison query."""
        # Use RAG engine to retrieve comparison data
        # Use agent system for cross-report comparison
        # For now, return placeholder
        return {
            "summary": f"Comparison across {', '.join(dimensions)}",
            "explanation": "Comparison results",
            "sources": [],
            "metrics": {},
            "confidence": 0.8,
        }

    def _extract_scenario_parameters(self, query: str) -> Dict[str, Any]:
        """Extract scenario parameters from query."""
        # Simple extraction (can be enhanced with LLM)
        scenario = {}
        if "increase" in query.lower() or "decrease" in query.lower():
            # Extract percentage changes
            scenario["type"] = "parameter_change"
        return scenario

    def _execute_simulation(
        self,
        query: str,
        scenario: Dict[str, Any],
        bank_id: str,
    ) -> Dict[str, Any]:
        """Execute what-if simulation."""
        # Use simulation agent for scenario execution
        # For now, return placeholder
        return {
            "summary": "Simulation results",
            "explanation": "What-if scenario analysis",
            "sources": [],
            "metrics": {},
            "confidence": 0.75,
        }

