"""
CrewAI setup for ML agent orchestration.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

from payscope_processing.llm.openai_o1 import OpenAIO1Client
from payscope_processing.llm.tgi_client import TGIClient


class MLAgentCrew:
    """
    CrewAI orchestration for ML tasks.
    
    Agents:
    - Feature Engineer: Analyzes data and suggests features
    - Model Selector: Chooses appropriate models
    - Hyperparameter Tuner: Optimizes hyperparameters
    - Evaluator: Evaluates model performance
    """

    def __init__(
        self,
        use_o1: bool = True,
        use_llama: bool = False,
        tgi_url: str = None,
        openai_key: str = None,
    ):
        self.use_o1 = use_o1
        self.use_llama = use_llama
        
        # Initialize LLM clients
        if use_o1:
            self.o1_client = OpenAIO1Client(api_key=openai_key)
            self.llm = ChatOpenAI(
                model="o1-preview",
                api_key=openai_key or os.getenv("OPENAI_API_KEY"),
                temperature=1.0,
            )
        elif use_llama:
            self.tgi_client = TGIClient(base_url=tgi_url)
            # For CrewAI, we'd need a LangChain TGI integration
            # Using OpenAI as fallback for now
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        else:
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    def create_feature_engineer_agent(self) -> Agent:
        """Agent for feature engineering."""
        return Agent(
            role="Feature Engineering Specialist",
            goal="Analyze datasets and suggest optimal features for ML models",
            backstory="Expert in feature engineering with deep understanding of financial fraud patterns and time-series data.",
            llm=self.llm,
            verbose=True,
        )

    def create_model_selector_agent(self) -> Agent:
        """Agent for model selection."""
        return Agent(
            role="ML Model Selection Expert",
            goal="Select the best ML models for fraud detection and forecasting tasks",
            backstory="Data scientist specializing in model selection for financial ML applications.",
            llm=self.llm,
            verbose=True,
        )

    def create_hyperparameter_tuner_agent(self) -> Agent:
        """Agent for hyperparameter tuning."""
        return Agent(
            role="Hyperparameter Optimization Specialist",
            goal="Optimize hyperparameters for selected ML models",
            backstory="ML engineer expert in hyperparameter tuning and model optimization.",
            llm=self.llm,
            verbose=True,
        )

    def create_evaluator_agent(self) -> Agent:
        """Agent for model evaluation."""
        return Agent(
            role="Model Evaluation Expert",
            goal="Evaluate model performance and provide insights",
            backstory="ML researcher specializing in model evaluation metrics and performance analysis.",
            llm=self.llm,
            verbose=True,
        )

    def orchestrate_ml_pipeline(
        self,
        task_description: str,
        data_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Orchestrate ML pipeline using CrewAI agents.
        
        Returns:
            Dict with recommendations and decisions
        """
        # Create agents
        feature_engineer = self.create_feature_engineer_agent()
        model_selector = self.create_model_selector_agent()
        hyperparameter_tuner = self.create_hyperparameter_tuner_agent()
        evaluator = self.create_evaluator_agent()

        # Create tasks
        feature_task = Task(
            description=f"""
            Analyze the dataset and suggest optimal features.
            Data summary: {data_summary}
            Task: {task_description}
            
            Provide:
            1. Recommended features
            2. Feature engineering steps
            3. Feature importance insights
            """,
            agent=feature_engineer,
            expected_output="JSON with feature recommendations",
        )

        model_task = Task(
            description=f"""
            Based on the features and task, select appropriate ML models.
            Task: {task_description}
            
            Provide:
            1. Recommended model type(s)
            2. Rationale for selection
            3. Expected performance characteristics
            """,
            agent=model_selector,
            expected_output="JSON with model recommendations",
        )

        tuning_task = Task(
            description=f"""
            Suggest hyperparameter configurations for the selected models.
            Task: {task_description}
            
            Provide:
            1. Hyperparameter search space
            2. Recommended starting values
            3. Optimization strategy
            """,
            agent=hyperparameter_tuner,
            expected_output="JSON with hyperparameter recommendations",
        )

        evaluation_task = Task(
            description=f"""
            Define evaluation metrics and validation strategy.
            Task: {task_description}
            
            Provide:
            1. Recommended metrics
            2. Validation strategy
            3. Success criteria
            """,
            agent=evaluator,
            expected_output="JSON with evaluation strategy",
        )

        # Create crew
        crew = Crew(
            agents=[feature_engineer, model_selector, hyperparameter_tuner, evaluator],
            tasks=[feature_task, model_task, tuning_task, evaluation_task],
            process=Process.sequential,  # Sequential execution
            verbose=True,
        )

        # Execute
        result = crew.kickoff()
        
        return {
            "recommendations": str(result),
            "agents_used": ["feature_engineer", "model_selector", "hyperparameter_tuner", "evaluator"],
        }


def get_ml_crew(use_o1: bool = True, use_llama: bool = False) -> MLAgentCrew:
    """Get configured ML agent crew."""
    return MLAgentCrew(use_o1=use_o1, use_llama=use_llama)



