#!/usr/bin/env python3
"""
Test script for free LLM client.

Tests OpenAI-compatible interface with HF Inference API or local fallback.
"""

import os
import sys
from pathlib import Path

# Add processing src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "processing" / "src"))

from payscope_processing.llm.free_client import FreeLLMClient


def main():
    """Test free LLM client."""
    print("=" * 60)
    print("Free LLM Client Test")
    print("=" * 60)
    print()
    
    # Check environment
    print("Environment Check:")
    hf_token = os.getenv("HF_API_TOKEN")
    if hf_token:
        print(f"  ✓ HF_API_TOKEN: {hf_token[:10]}..." + " (set)")
    else:
        print("  ✗ HF_API_TOKEN: (not set)")
    
    provider = os.getenv("LLM_PROVIDER", "auto")
    print(f"  LLM_PROVIDER: {provider}")
    print()
    
    # Create client
    print("Initializing client...")
    try:
        client = FreeLLMClient()
        print(f"  ✓ Using provider: {client.get_provider()}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print()
        print("Setup options:")
        print("  1. Set HF_API_TOKEN for Hugging Face Inference API")
        print("  2. Start Ollama: ollama serve && ollama pull llama3.1:8b")
        print("  3. Start vLLM: python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.1-8B-Instruct")
        return 1
    
    print()
    
    # Test message
    print("Sending test message...")
    messages = [
        {"role": "user", "content": "Hello! Please respond with a brief greeting."}
    ]
    
    try:
        response = client.chat_completions(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print("Response:")
        print("-" * 60)
        
        # Extract content
        content = response["choices"][0]["message"]["content"]
        print(content)
        
        print("-" * 60)
        print()
        print(f"Model: {response.get('model', 'unknown')}")
        print(f"Provider: {client.get_provider()}")
        print()
        print("✓ Test successful!")
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())



