"""
LLM client modules.

Supports multiple providers:
- OpenAI-compatible APIs
- Hugging Face Inference API (free tier)
- Local Ollama/vLLM (free, self-hosted)
- TGI (Text Generation Inference)
"""

from payscope_processing.llm.free_client import FreeLLMClient, chat_json
from payscope_processing.llm.hf_client import HuggingFaceInferenceClient, create_hf_client
from payscope_processing.llm.local_client import OllamaClient, VLLMClient, create_local_client

__all__ = [
    "FreeLLMClient",
    "HuggingFaceInferenceClient",
    "OllamaClient",
    "VLLMClient",
    "create_hf_client",
    "create_local_client",
    "chat_json",
]



