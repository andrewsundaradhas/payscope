"""
CrewAI + LangChain agent for forecasting ML tasks.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from payscope_processing.ml_agents.crew_setup import MLAgentCrew


class ForecastingAgent:
    """
    Agent-powered forecasting model training.
    
    Uses CrewAI agents to:
    - Analyze time-series patterns
    - Suggest forecasting models
    - Recommend hyperparameters
    - Optimize seasonality detection
    """

    def __init__(self, crew: MLAgentCrew = None):
        self.crew = crew or MLAgentCrew(use_o1=True)

    def analyze_time_series(
        self,
        df: pd.DataFrame,
        time_column: str,
        target_column: str,
        bank_id: int,
    ) -> Dict[str, Any]:
        """
        Use agents to analyze time-series data and provide recommendations.
        
        Returns:
            Dict with model recommendations, seasonality insights, etc.
        """
        # Summarize time-series
        df_ts = df[[time_column, target_column]].copy()
        df_ts[time_column] = pd.to_datetime(df_ts[time_column], errors="coerce")
        df_ts = df_ts.dropna()
        
        data_summary = {
            "total_points": len(df_ts),
            "date_range": {
                "start": str(df_ts[time_column].min()),
                "end": str(df_ts[time_column].max()),
            },
            "target_stats": {
                "mean": float(df_ts[target_column].mean()),
                "std": float(df_ts[target_column].std()),
                "min": float(df_ts[target_column].min()),
                "max": float(df_ts[target_column].max()),
            },
        }

        task_description = f"""
        Time-Series Forecasting for Bank {bank_id}
        
        Dataset characteristics:
        - Time points: {len(df_ts):,}
        - Date range: {df_ts[time_column].min()} to {df_ts[time_column].max()}
        - Target: {target_column}
        
        Goal: Build accurate forecasting models with proper seasonality handling.
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



