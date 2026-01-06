"""
CrewAI + LangChain agent for fraud detection ML tasks.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd

from payscope_processing.ml_agents.crew_setup import MLAgentCrew


class FraudDetectionAgent:
    """
    Agent-powered fraud detection model training.
    
    Uses CrewAI agents to:
    - Analyze fraud patterns
    - Suggest features
    - Recommend models
    - Optimize hyperparameters
    """

    def __init__(self, crew: MLAgentCrew = None):
        self.crew = crew or MLAgentCrew(use_o1=True)

    def analyze_fraud_data(
        self,
        df: pd.DataFrame,
        fraud_column: str,
        bank_id: int,
    ) -> Dict[str, Any]:
        """
        Use agents to analyze fraud data and provide recommendations.
        
        Returns:
            Dict with feature recommendations, model suggestions, etc.
        """
        # Summarize data
        fraud_count = df[fraud_column].sum() if fraud_column in df.columns else 0
        fraud_rate = fraud_count / len(df) if len(df) > 0 else 0
        
        data_summary = {
            "total_rows": len(df),
            "fraud_count": int(fraud_count),
            "fraud_rate": float(fraud_rate),
            "numeric_features": len(df.select_dtypes(include=["number"]).columns),
            "categorical_features": len(df.select_dtypes(include=["object"]).columns),
            "columns": list(df.columns)[:20],  # First 20 columns
        }

        task_description = f"""
        Fraud Detection Model Training for Bank {bank_id}
        
        Dataset characteristics:
        - Total transactions: {len(df):,}
        - Fraud cases: {fraud_count:,} ({fraud_rate*100:.2f}%)
        - This is a highly imbalanced dataset
        
        Goal: Build an effective fraud detection model with high recall while maintaining precision.
        """

        # Orchestrate agent pipeline
        recommendations = self.crew.orchestrate_ml_pipeline(
            task_description=task_description,
            data_summary=data_summary,
        )

        return {
            "bank_id": bank_id,
            "data_summary": data_summary,
            "recommendations": recommendations,
        }

    def suggest_features(self, df: pd.DataFrame, fraud_column: str) -> List[str]:
        """
        Use agent to suggest optimal features.
        
        Returns:
            List of recommended feature names
        """
        analysis = self.analyze_fraud_data(df, fraud_column, bank_id=0)
        # Parse recommendations to extract features
        # This is a simplified version - in practice, parse JSON from agent output
        numeric_features = df.select_dtypes(include=["number"]).columns.tolist()
        if fraud_column in numeric_features:
            numeric_features.remove(fraud_column)
        return numeric_features[:30]  # Top 30 features



