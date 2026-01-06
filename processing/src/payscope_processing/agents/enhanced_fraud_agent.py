"""
Enhanced fraud agent with LLM integration.
"""

from __future__ import annotations

from typing import Any, Dict, List

from payscope_processing.agents.base import AgentLogRecord
from payscope_processing.agents.enhanced_base import EnhancedAgentBase


class EnhancedFraudAgent(EnhancedAgentBase):
    """
    Enhanced fraud agent with LLM-assisted reasoning.
    
    Maintains compatibility with existing FraudAgent while adding LLM capabilities.
    """

    name = "EnhancedFraudAgent"
    tools = ["graph_read", "vector_memory_read", "llm_reasoning"]

    def run(self, task_id: str, *, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze anomalies with optional LLM assistance.
        """
        scores = []
        rationale = []

        # Base rule-based scoring (deterministic fallback)
        for a in anomalies:
            risk = 0.1
            if a.get("missing_settlement"):
                risk += 0.3
            if a.get("has_amount_mismatch"):
                risk += 0.25
            if a.get("currency_conflict"):
                risk += 0.15
            if a.get("timestamp_violation"):
                risk += 0.1
            gap = a.get("lifecycle_gap_duration")
            if gap and gap > 86400:
                risk += 0.1
            risk = min(1.0, risk)

            # LLM-assisted refinement if available
            if self.use_llm and len(anomalies) <= 50:  # Limit LLM calls
                llm_prompt = f"""
                Analyze this fraud anomaly:
                - Missing settlement: {a.get('missing_settlement', False)}
                - Amount mismatch: {a.get('has_amount_mismatch', False)}
                - Currency conflict: {a.get('currency_conflict', False)}
                - Timestamp violation: {a.get('timestamp_violation', False)}
                - Lifecycle gap: {gap} seconds
                
                Base risk score: {risk:.2f}
                
                Provide a refined risk score (0.0-1.0) and brief rationale.
                Format: RISK: <score> | RATIONALE: <text>
                """
                
                llm_response = self._llm_call(
                    system_prompt="You are an expert fraud detection analyst.",
                    user_prompt=llm_prompt,
                )
                
                # Parse LLM response (fallback to base score if parsing fails)
                try:
                    if "RISK:" in llm_response:
                        refined_risk = float(llm_response.split("RISK:")[1].split("|")[0].strip())
                        refined_risk = max(0.0, min(1.0, refined_risk))  # Clamp
                        risk = (risk + refined_risk) / 2  # Blend base and LLM scores
                    if "RATIONALE:" in llm_response:
                        rationale_text = llm_response.split("RATIONALE:")[1].strip()
                        rationale.append(rationale_text)
                except Exception:
                    pass  # Use base score on parse failure

            scores.append({
                "transaction_id": a.get("transaction_id"),
                "fraud_risk_score": risk,
                "llm_refined": self.use_llm,
            })

        output = {
            "fraud_scores": scores,
            "llm_used": self.use_llm,
            "rationale": rationale if rationale else None,
        }

        self.log_action(
            AgentLogRecord(
                agent_name=self.name,
                task_id=task_id,
                inputs={"anomalies": anomalies},
                outputs=output,
                confidence=0.85 if self.use_llm else 0.8,
                decision_rationale="LLM-assisted fraud detection" if self.use_llm else "rule-based risk scoring",
            )
        )
        return output



