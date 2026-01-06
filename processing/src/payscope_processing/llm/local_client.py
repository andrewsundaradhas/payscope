"""
Local self-hosted LLM client (Ollama/vLLM).

Fallback option when HF API is not available.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama client with OpenAI-compatible interface.
    
    Requires local Ollama server running:
    - Install: https://ollama.ai
    - Run: ollama pull llama3.1:8b
    - Server runs on http://localhost:11434
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL (default: localhost:11434)
            model: Model name (default: llama3.1:8b)
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx not installed. Install it: pip install httpx"
            )
        
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=120.0)
        logger.info(f"Initialized Ollama client: {base_url}, model: {model}")

    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completions endpoint.
        
        Ollama has native OpenAI-compatible endpoint at /v1/chat/completions
        """
        model_name = model or self.model
        
        # Ollama OpenAI-compatible endpoint
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama connection failed: {e}") from e


class VLLMClient:
    """
    vLLM client with OpenAI-compatible interface.
    
    Requires local vLLM server running:
    - Install: pip install vllm
    - Run: python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.1-8B-Instruct
    - Server runs on http://localhost:8000/v1
    """

    def __init__(self, base_url: str = "http://localhost:8000", model: str = "meta-llama/Llama-3.1-8B-Instruct"):
        """
        Initialize vLLM client.
        
        Args:
            base_url: vLLM server URL (default: localhost:8000)
            model: Model name (default: LLaMA 3.1 8B Instruct)
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx not installed. Install it: pip install httpx"
            )
        
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=120.0)
        logger.info(f"Initialized vLLM client: {base_url}, model: {model}")

    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completions endpoint.
        
        vLLM provides OpenAI-compatible endpoint at /v1/chat/completions
        """
        model_name = model or self.model
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"vLLM API error: {e}")
            raise RuntimeError(f"vLLM connection failed: {e}") from e


def create_local_client(provider: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
    """
    Factory function to create local LLM client.
    
    Args:
        provider: "ollama" or "vllm" (auto-detects if None)
        base_url: Server base URL (auto-detects if None)
        model: Model name (uses defaults if None)
    
    Returns:
        OllamaClient or VLLMClient instance
    
    Raises:
        RuntimeError: If neither server is available
    """
    import httpx
    
    provider = provider or os.getenv("LLM_LOCAL_PROVIDER", "ollama").lower()
    base_url = base_url or os.getenv("LLM_LOCAL_BASE_URL")
    
    # Try Ollama first (simpler, no GPU required)
    if provider == "ollama" or (not base_url and provider != "vllm"):
        ollama_url = base_url or "http://localhost:11434"
        ollama_model = model or os.getenv("LLM_LOCAL_MODEL", "llama3.1:8b")
        
        try:
            client = httpx.Client(timeout=5.0)
            response = client.get(f"{ollama_url}/api/tags")
            response.raise_for_status()
            logger.info("Ollama server detected")
            return OllamaClient(base_url=ollama_url, model=ollama_model)
        except Exception:
            logger.debug("Ollama server not available, trying vLLM")
    
    # Try vLLM
    vllm_url = base_url or "http://localhost:8000"
    vllm_model = model or os.getenv("LLM_LOCAL_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(f"{vllm_url}/health")
        response.raise_for_status()
        logger.info("vLLM server detected")
        return VLLMClient(base_url=vllm_url, model=vllm_model)
    except Exception:
        raise RuntimeError(
            "No local LLM server found. Start Ollama (ollama serve) or vLLM server."
        )



