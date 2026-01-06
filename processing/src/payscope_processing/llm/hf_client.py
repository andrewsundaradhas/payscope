"""
Hugging Face Inference API client (OpenAI-compatible).

Provides free-tier access to LLaMA 3.1 via HF Inference API.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HuggingFaceInferenceClient:
    """
    Hugging Face Inference API client with OpenAI-compatible interface.
    
    Uses free-tier HF Inference API for LLaMA 3.1.
    """

    def __init__(self, api_token: str, model: str = "meta-llama/Llama-3.1-8B-Instruct"):
        """
        Initialize HF Inference client.
        
        Args:
            api_token: Hugging Face API token (free tier works)
            model: Model identifier (default: LLaMA 3.1 8B Instruct)
        """
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError(
                "huggingface_hub not installed. Install it: pip install huggingface_hub"
            )
        
        self.client = InferenceClient(token=api_token, model=model)
        self.model = model
        self.api_token = api_token
        logger.info(f"Initialized HF Inference client with model: {model}")

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
            model: Model name (optional, uses instance default)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters (ignored for HF API)
        
        Returns:
            OpenAI-compatible response dict
        """
        # Convert OpenAI message format to HF format
        prompt = self._messages_to_prompt(messages)
        
        # HF Inference API parameters
        params: Dict[str, Any] = {
            "temperature": temperature,
        }
        if max_tokens:
            params["max_new_tokens"] = max_tokens
        
        try:
            # Call HF Inference API
            response_text = self.client.text_generation(
                prompt=prompt,
                **params
            )
            
            # Extract just the generated text (remove prompt if included)
            if response_text.startswith(prompt):
                generated_text = response_text[len(prompt):].strip()
            else:
                generated_text = response_text.strip()
            
            # Format as OpenAI response
            return self._format_openai_response(generated_text, model or self.model)
            
        except Exception as e:
            logger.error(f"HF Inference API error: {e}")
            # Check if it's a quota/rate limit error
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str or "limit" in error_str:
                raise RuntimeError("HF_API_QUOTA_EXCEEDED") from e
            raise

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI message format to LLaMA prompt format.
        
        LLaMA 3.1 uses:
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        {system_message}<|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        {user_message}<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
        prompt_parts = ["<|begin_of_text|>"]
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append("<|start_header_id|>system<|end_header_id|>")
                prompt_parts.append(f"\n\n{content}<|eot_id|>")
            elif role == "user":
                prompt_parts.append("<|start_header_id|>user<|end_header_id|>")
                prompt_parts.append(f"\n\n{content}<|eot_id|>")
            elif role == "assistant":
                prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>")
                prompt_parts.append(f"\n\n{content}<|eot_id|>")
        
        # Add assistant header for generation
        prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>")
        prompt_parts.append("\n\n")
        
        return "".join(prompt_parts)

    def _format_openai_response(self, content: str, model: str) -> Dict[str, Any]:
        """
        Format HF response as OpenAI-compatible response.
        """
        return {
            "id": f"chatcmpl-{os.urandom(16).hex()}",
            "object": "chat.completion",
            "created": int(os.path.getmtime(__file__)),  # Simple timestamp
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,  # HF API doesn't provide token counts in free tier
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }


def create_hf_client(api_token: Optional[str] = None, model: Optional[str] = None) -> Optional[HuggingFaceInferenceClient]:
    """
    Factory function to create HF Inference client if token is available.
    
    Args:
        api_token: HF API token (if None, reads from HF_API_TOKEN env var)
        model: Model name (optional)
    
    Returns:
        HuggingFaceInferenceClient instance or None if no token
    """
    token = api_token or os.getenv("HF_API_TOKEN")
    if not token:
        return None
    
    model_name = model or os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    return HuggingFaceInferenceClient(api_token=token, model=model_name)



