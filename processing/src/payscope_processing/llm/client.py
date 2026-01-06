from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    timeout_s: float = 30.0
    # Free LLM options (optional, for free LLM provider)
    llm_provider: str | None = None
    hf_api_token: str | None = None
    llm_local_provider: str | None = None
    llm_local_base_url: str | None = None
    llm_local_model: str | None = None


class LlmError(RuntimeError):
    pass


def chat_json(
    *,
    cfg: LlmConfig,
    system: str,
    user: str,
    response_json_schema: dict[str, Any],
) -> dict[str, Any]:
    """
    OpenAI-compatible chat completions call with deterministic settings:
      - temperature=0
      - top_p=1

    Enforces a strict JSON response contract by parsing returned content as JSON.
    
    Supports both paid OpenAI-compatible APIs and free LLM providers (HF Inference API, Ollama, vLLM).
    Automatically selects free LLM if configured, otherwise uses the provided base_url/api_key.
    """
    # Check if free LLM should be used
    use_free_llm = False
    
    # Use free LLM if:
    # 1. llm_provider is set to "hf", "local", or "auto"
    # 2. OR if base_url/api_key are not provided
    provider = cfg.llm_provider or os.getenv("LLM_PROVIDER", "openai")
    if provider in ("hf", "local", "auto") or (not cfg.base_url or not cfg.api_key):
        use_free_llm = True
    
    if use_free_llm:
        try:
            from payscope_processing.llm.free_client import FreeLLMClient
            
            # Initialize free LLM client
            hf_token = cfg.hf_api_token or os.getenv("HF_API_TOKEN")
            local_provider = cfg.llm_local_provider or os.getenv("LLM_LOCAL_PROVIDER", "ollama")
            local_base_url = cfg.llm_local_base_url or os.getenv("LLM_LOCAL_BASE_URL")
            local_model = cfg.llm_local_model or os.getenv("LLM_LOCAL_MODEL")
            
            free_client = FreeLLMClient(
                provider=provider,
                hf_token=hf_token,
                local_provider=local_provider,
                model=local_model or cfg.model
            )
            
            # Convert to OpenAI message format
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            
            # Call free LLM (note: response_format may not be fully supported, but we'll try)
            response = free_client.chat_completions(
                messages=messages,
                temperature=0.0,
                max_tokens=1024,
                response_format={
                    "type": "json_object" if response_json_schema else "text",
                } if response_json_schema else None,
            )
            
            # Extract content
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON
            try:
                if isinstance(content, dict):
                    return content
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON from text
                logger.warning(f"Failed to parse JSON directly, attempting extraction: {e}")
                # Try to find JSON block in response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise LlmError(f"llm_invalid_json_response: {e}")
                
        except ImportError:
            logger.warning("Free LLM client not available, falling back to HTTP client")
            use_free_llm = False
        except Exception as e:
            logger.warning(f"Free LLM failed: {e}, falling back to HTTP client")
            use_free_llm = False
    
    # Fallback to HTTP-based OpenAI-compatible API
    if not use_free_llm:
        if not cfg.base_url or not cfg.api_key:
            raise LlmError("llm_not_configured: LLM_BASE_URL and LLM_API_KEY required, or configure free LLM (HF_API_TOKEN or local server)")
        
        url = cfg.base_url.rstrip("/") + "/v1/chat/completions"
        headers = {"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"}

        payload: dict[str, Any] = {
            "model": cfg.model,
            "temperature": 0,
            "top_p": 1,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Best-effort schema guidance (supported by some providers).
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "mapping_response", "schema": response_json_schema},
            },
        }

        with httpx.Client(timeout=cfg.timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                raise LlmError(f"llm_http_error status={r.status_code} body={r.text[:500]}")
            data = r.json()

        try:
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, dict):
                return content
            return json.loads(content)
        except Exception as e:
            raise LlmError(f"llm_invalid_json_response: {e}")


