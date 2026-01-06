"""
HuggingFace Text Generation Inference (TGI) client for LLaMA 3.1.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class TGIClient:
    """
    Client for HuggingFace TGI server (LLaMA 3.1).
    
    Requires TGI server running (e.g., docker run -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest)
    """

    def __init__(self, base_url: str = None, timeout: float = 60.0):
        self.base_url = base_url or os.getenv("TGI_BASE_URL", "http://localhost:8080")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ) -> str:
        """
        Generate text using TGI.
        
        Returns generated text.
        """
        response = self._client.post(
            f"{self.base_url}/generate",
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    **kwargs,
                },
            },
        )
        response.raise_for_status()
        result = response.json()
        return result.get("generated_text", "")

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Stream generated text.
        
        Yields text chunks.
        """
        with httpx.stream(
            "POST",
            f"{self.base_url}/generate_stream",
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    **kwargs,
                },
            },
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    yield line

    def close(self):
        """Close HTTP client."""
        self._client.close()


def get_tgi_client() -> TGIClient:
    """Get configured TGI client."""
    return TGIClient()




