"""
Free LLM client adapter (HF Inference API + Local fallback).

Provides OpenAI-compatible interface with automatic provider selection:
1. Hugging Face Inference API (free tier)
2. Local Ollama/vLLM (fallback)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from payscope_processing.llm.hf_client import HuggingFaceInferenceClient, create_hf_client
from payscope_processing.llm.local_client import create_local_client

logger = logging.getLogger(__name__)


class FreeLLMClient:
    """
    Free LLM client with automatic provider selection.
    
    Tries providers in order:
    1. Hugging Face Inference API (if HF_API_TOKEN set)
    2. Local Ollama/vLLM (fallback)
    
    Provides OpenAI-compatible interface.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        hf_token: Optional[str] = None,
        local_provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize free LLM client.
        
        Args:
            provider: "hf" or "local" (auto-selects if None)
            hf_token: HF API token (reads from env if None)
            local_provider: "ollama" or "vllm" (auto-detects if None)
            model: Model name (optional)
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "auto")
        self.client: Any = None
        self.current_provider_name = "none"
        
        # Try HF first if provider is "hf" or "auto"
        if self.provider in ("hf", "auto"):
            try:
                hf_client = create_hf_client(api_token=hf_token, model=model)
                if hf_client:
                    self.client = hf_client
                    self.current_provider_name = "huggingface"
                    logger.info("Using Hugging Face Inference API")
                    return
            except Exception as e:
                logger.warning(f"HF Inference API unavailable: {e}")
        
        # Fallback to local if provider is "local" or "auto"
        if self.provider in ("local", "auto"):
            try:
                # Get base_url from env if not provided via settings
                base_url = os.getenv("LLM_LOCAL_BASE_URL")
                self.client = create_local_client(
                    provider=local_provider,
                    base_url=base_url,
                    model=model
                )
                self.current_provider_name = "local"
                logger.info(f"Using local LLM: {type(self.client).__name__}")
                return
            except Exception as e:
                logger.warning(f"Local LLM unavailable: {e}")
        
        # No provider available
        if not self.client:
            raise RuntimeError(
                "No LLM provider available. Set HF_API_TOKEN or start local server (Ollama/vLLM)."
            )

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
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            OpenAI-compatible response dict
        
        Raises:
            RuntimeError: If provider fails and no fallback available
        """
        try:
            return self.client.chat_completions(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        except RuntimeError as e:
            # Check if it's a quota error from HF
            if "HF_API_QUOTA_EXCEEDED" in str(e) and self.current_provider_name == "huggingface":
                logger.warning("HF API quota exceeded, attempting fallback to local...")
                # Try to fallback to local
                try:
                    self.client = create_local_client(model=model)
                    self.current_provider_name = "local"
                    logger.info("Fell back to local LLM")
                    return self.client.chat_completions(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                except Exception:
                    pass
            raise

    def get_provider(self) -> str:
        """Get current provider name."""
        return self.current_provider_name


# Convenience function for existing code
def chat_json(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Simplified chat interface for JSON responses.
    
    Args:
        messages: List of message dicts
        system: System message (prepended if provided)
        temperature: Sampling temperature
        max_tokens: Max tokens
        **kwargs: Additional parameters
    
    Returns:
        Response dict with 'content' key
    """
    client = FreeLLMClient()
    
    # Prepend system message if provided
    if system:
        msgs = [{"role": "system", "content": system}] + messages
    else:
        msgs = messages
    
    response = client.chat_completions(
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    # Extract content from OpenAI format
    content = response["choices"][0]["message"]["content"]
    
    # Try to parse as JSON if it looks like JSON
    try:
        return json.loads(content)
    except (json.JSONDecodeError, KeyError):
        return {"content": content}

