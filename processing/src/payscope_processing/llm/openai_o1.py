"""
OpenAI o1 client for advanced reasoning tasks.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI


class OpenAIO1Client:
    """
    Client for OpenAI o1 models (o1-preview, o1-mini).
    
    Supports reasoning tasks for ML analysis and decision-making.
    """

    def __init__(self, api_key: str = None, model: str = "o1-preview"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        self.model = model
        self._client = OpenAI(api_key=self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,  # o1 models ignore temperature
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        """
        Chat completion with o1 model.
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
        
        Returns:
            Assistant response text
        """
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content

    def analyze(
        self,
        task: str,
        context: str,
        system_prompt: str = "You are an expert ML engineer and data scientist.",
    ) -> str:
        """
        Analyze a task with context using o1 reasoning.
        
        Returns analysis/decision.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Task: {task}\n\nContext:\n{context}\n\nProvide your analysis:",
            },
        ]
        return self.chat(messages)


def get_openai_o1_client() -> OpenAIO1Client:
    """Get configured OpenAI o1 client."""
    return OpenAIO1Client()




