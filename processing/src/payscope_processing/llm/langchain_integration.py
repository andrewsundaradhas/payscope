"""
LangChain integration for LLM backends (TGI + OpenAI o1).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

try:
    from langchain_community.llms import HuggingFaceTextGenInference
    TGI_AVAILABLE = True
except ImportError:
    TGI_AVAILABLE = False

from payscope_processing.llm.openai_o1 import OpenAIO1Client
from payscope_processing.llm.tgi_client import TGIClient


def get_llm_backend(
    backend: str = "openai_o1",
    tgi_url: str = None,
    openai_key: str = None,
) -> BaseLanguageModel:
    """
    Get LangChain LLM backend.
    
    Args:
        backend: "openai_o1" | "tgi" | "openai_gpt4"
        tgi_url: TGI server URL (default: from env)
        openai_key: OpenAI API key (default: from env)
    
    Returns:
        LangChain LLM instance
    """
    tgi_url = tgi_url or os.getenv("TGI_BASE_URL", "http://localhost:8080")
    openai_key = openai_key or os.getenv("OPENAI_API_KEY")

    if backend == "openai_o1":
        if not openai_key:
            raise ValueError("OPENAI_API_KEY required for o1")
        return ChatOpenAI(
            model="o1-preview",
            api_key=openai_key,
            temperature=1.0,  # o1 ignores this but required
        )
    elif backend == "tgi":
        if TGI_AVAILABLE:
            return HuggingFaceTextGenInference(
                inference_server_url=tgi_url,
                max_new_tokens=512,
                temperature=0.7,
            )
        else:
            raise ValueError("langchain_community not installed. Install: pip install langchain-community")
    elif backend == "openai_gpt4":
        if not openai_key:
            raise ValueError("OPENAI_API_KEY required")
        return ChatOpenAI(model="gpt-4", api_key=openai_key, temperature=0.7)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def create_agent_llm(use_o1: bool = True) -> BaseLanguageModel:
    """
    Create LLM for agent use.
    
    Prefers o1 for reasoning, falls back to GPT-4, then TGI.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    tgi_url = os.getenv("TGI_BASE_URL", "http://localhost:8080")

    if use_o1 and openai_key:
        try:
            return get_llm_backend("openai_o1", openai_key=openai_key)
        except Exception:
            pass

    if openai_key:
        try:
            return get_llm_backend("openai_gpt4", openai_key=openai_key)
        except Exception:
            pass

    if TGI_AVAILABLE:
        try:
            return get_llm_backend("tgi", tgi_url=tgi_url)
        except Exception:
            pass

    # Fallback: raise error
    raise RuntimeError("No LLM backend available. Configure OPENAI_API_KEY or TGI_BASE_URL")




