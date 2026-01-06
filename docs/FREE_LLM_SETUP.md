# Free LLaMA 3.1 Setup Guide

This guide shows how to set up a **free, OpenAI-compatible API** for LLaMA 3.1 using legal, free options.

## Overview

PayScope supports two free LLM providers:

1. **Hugging Face Inference API** (Preferred - no setup required)
2. **Local Self-Hosted** (Ollama or vLLM - guaranteed free)

The system automatically selects the best available option.

---

## Option 1: Hugging Face Inference API (Recommended)

### Requirements

- **Free**: Yes, free tier available
- **Setup Time**: 2 minutes
- **GPU**: Not required (runs on HF servers)
- **Internet**: Required

### Step 1: Get Free HF Token

1. Go to https://huggingface.co/
2. Sign up for free account
3. Navigate to Settings → Access Tokens
4. Create a new token (read access is sufficient)
5. Copy the token (starts with `hf_`)

### Step 2: Configure

Add to your `.env` file:

```env
HF_API_TOKEN=hf_your_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
LLM_PROVIDER=hf
```

### Step 3: Install Dependencies

```powershell
pip install huggingface_hub
```

Or with Poetry:

```powershell
poetry add huggingface_hub
```

### Step 4: Test

```powershell
python scripts/test_free_llm.py
```

### Limits

- **Free Tier**: ~1000 requests/day
- **Rate Limits**: ~30 requests/minute
- **Model**: LLaMA 3.1 8B Instruct (or other HF-hosted models)

**Note**: If you hit quota limits, the system automatically falls back to local options.

---

## Option 2: Local Self-Hosted (Ollama)

### Requirements

- **Free**: Yes, completely free
- **Setup Time**: 5-10 minutes
- **GPU**: Optional (CPU works but slower)
- **Internet**: Required for initial download only

### Step 1: Install Ollama

**Windows:**
1. Download from https://ollama.ai/download
2. Run installer
3. Ollama service starts automatically

**Linux/Mac:**
```bash
curl https://ollama.ai/install.sh | sh
```

### Step 2: Pull LLaMA 3.1 Model

```powershell
ollama pull llama3.1:8b
```

This downloads ~4.7GB (one-time download).

### Step 3: Verify Ollama is Running

```powershell
ollama serve
```

Should start server on `http://localhost:11434`

### Step 4: Configure

Add to your `.env` file:

```env
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=ollama
LLM_LOCAL_MODEL=llama3.1:8b
```

### Step 5: Test

```powershell
python scripts/test_free_llm.py
```

### Performance

- **CPU**: ~5-10 tokens/second (usable for testing)
- **GPU**: ~50+ tokens/second (recommended for production)
- **Memory**: ~8GB RAM required

---

## Option 3: Local Self-Hosted (vLLM)

### Requirements

- **Free**: Yes, completely free
- **Setup Time**: 15-20 minutes
- **GPU**: Required (CUDA-compatible)
- **Internet**: Required for initial download

### Step 1: Install vLLM

**Prerequisites:**
- CUDA 11.8+ installed
- Python 3.8+

```powershell
pip install vllm
```

### Step 2: Start vLLM Server

```powershell
python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.1-8B-Instruct --port 8000
```

Server starts on `http://localhost:8000`

### Step 3: Configure

Add to your `.env` file:

```env
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=vllm
LLM_LOCAL_BASE_URL=http://localhost:8000
LLM_LOCAL_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### Step 4: Test

```powershell
python scripts/test_free_llm.py
```

### Performance

- **GPU**: ~100+ tokens/second
- **Memory**: ~16GB VRAM required (8B model)
- **Best for**: Production workloads

---

## Automatic Provider Selection

If you set `LLM_PROVIDER=auto` (default), the system tries providers in order:

1. **Hugging Face** (if `HF_API_TOKEN` is set)
2. **Local Ollama** (if server is running)
3. **Local vLLM** (if server is running)

**Fallback behavior:**
- If HF quota is exceeded → automatically falls back to local
- If local server unavailable → raises error with setup instructions

---

## Switching Providers

You can switch providers anytime by changing `.env`:

```env
# Use Hugging Face
LLM_PROVIDER=hf
HF_API_TOKEN=your_token

# Use Local Ollama
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=ollama

# Use Local vLLM
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=vllm

# Auto-select (tries HF first, then local)
LLM_PROVIDER=auto
```

**No code changes required!** The interface is OpenAI-compatible.

---

## API Usage

The free LLM client provides OpenAI-compatible interface:

```python
from payscope_processing.llm.free_client import FreeLLMClient

client = FreeLLMClient()

response = client.chat_completions(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=100
)

print(response["choices"][0]["message"]["content"])
```

Works exactly like OpenAI's API!

---

## Cost Comparison

| Provider | Cost | Setup | Performance |
|----------|------|-------|-------------|
| **HF Inference API** | Free (limited) | Easy | Good |
| **Ollama (CPU)** | Free | Easy | Slow |
| **Ollama (GPU)** | Free | Easy | Good |
| **vLLM (GPU)** | Free | Medium | Excellent |
| **OpenAI API** | $0.15/1M tokens | Easy | Excellent |

---

## Troubleshooting

### "No LLM provider available"

**Solution**: Set `HF_API_TOKEN` or start local server (Ollama/vLLM)

### "HF API quota exceeded"

**Solution**: System auto-falls back to local. Or wait for quota reset (daily).

### "Ollama connection failed"

**Solution**: 
1. Check if Ollama is running: `ollama serve`
2. Verify model is downloaded: `ollama list`
3. Pull model if missing: `ollama pull llama3.1:8b`

### "vLLM connection failed"

**Solution**:
1. Check if server is running: `curl http://localhost:8000/health`
2. Verify CUDA is available: `python -c "import torch; print(torch.cuda.is_available())"`
3. Check GPU memory: `nvidia-smi`

---

## Migration to OpenAI

When ready to use OpenAI, simply change `.env`:

```env
# Remove free LLM config
# HF_API_TOKEN=
# LLM_PROVIDER=

# Add OpenAI config
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key
LLM_MODEL=gpt-4o-mini
```

**No code changes needed!** The existing code uses the same interface.

---

## Summary

✅ **Free Options Available**: HF Inference API, Ollama, vLLM  
✅ **OpenAI-Compatible**: Drop-in replacement  
✅ **Auto-Fallback**: Handles quota limits automatically  
✅ **Zero Code Changes**: Switch providers via config  
✅ **Production Ready**: Used throughout PayScope  

Choose the option that best fits your needs!



