# Free LLaMA 3.1 - Quick Start

## 🎯 Goal

Set up a **free, OpenAI-compatible API** for LLaMA 3.1 without paying for API keys.

## ✅ What's Implemented

- ✅ **Hugging Face Inference API** client (free tier, no setup)
- ✅ **Local Ollama** client (self-hosted, free)
- ✅ **Local vLLM** client (self-hosted, GPU required)
- ✅ **Auto-selection** adapter (tries HF first, falls back to local)
- ✅ **OpenAI-compatible** interface

## 🚀 Quick Setup (Option 1: Hugging Face - Easiest)

### Step 1: Get Free Token (2 minutes)

1. Go to https://huggingface.co/
2. Sign up (free)
3. Settings → Access Tokens
4. Create token (read access)
5. Copy token (starts with `hf_`)

### Step 2: Add to .env

```env
HF_API_TOKEN=hf_your_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
LLM_PROVIDER=auto
```

### Step 3: Install

```powershell
pip install huggingface_hub
```

### Step 4: Test

```powershell
python scripts/test_free_llm.py
```

**Done!** You now have a free LLaMA 3.1 API.

---

## 🖥️ Quick Setup (Option 2: Local Ollama)

### Step 1: Install Ollama

Download from https://ollama.ai/download and install.

### Step 2: Pull Model

```powershell
ollama pull llama3.1:8b
```

### Step 3: Start Server

Ollama runs automatically. Verify:

```powershell
ollama serve
```

### Step 4: Configure .env

```env
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=ollama
LLM_LOCAL_MODEL=llama3.1:8b
```

### Step 5: Test

```powershell
python scripts/test_free_llm.py
```

**Done!** Completely free, runs locally.

---

## 📝 Usage

```python
from payscope_processing.llm.free_client import FreeLLMClient

client = FreeLLMClient()

response = client.chat_completions(
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=100
)

print(response["choices"][0]["message"]["content"])
```

Works exactly like OpenAI's API!

---

## 🔄 Switching Providers

Change `.env`:

```env
# Hugging Face (easiest)
HF_API_TOKEN=your_token
LLM_PROVIDER=hf

# Local Ollama (free, local)
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=ollama

# Local vLLM (GPU required)
LLM_PROVIDER=local
LLM_LOCAL_PROVIDER=vllm

# Auto (tries HF first, then local)
LLM_PROVIDER=auto
```

**No code changes needed!**

---

## 📚 Full Documentation

See `docs/FREE_LLM_SETUP.md` for complete guide including:
- Detailed setup instructions
- Troubleshooting
- Performance tips
- Migration to OpenAI

---

## ✅ Summary

✅ **Free**: HF API or local (both free)  
✅ **Easy**: 2-5 minutes setup  
✅ **OpenAI-Compatible**: Drop-in replacement  
✅ **Production Ready**: Used in PayScope  

Get started in 2 minutes with Hugging Face!



