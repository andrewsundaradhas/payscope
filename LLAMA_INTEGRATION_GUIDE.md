# LLaMA Integration Guide

PayScope now supports free LLaMA 3.1 integration via local Ollama or Hugging Face Inference API.

## Quick Start

### Option 1: Local Ollama (Recommended for local development)

1. **Install Ollama**: https://ollama.ai
2. **Download LLaMA 3.1**:
   ```bash
   ollama pull llama3.1:8b
   ```
3. **Start Ollama server**:
   ```bash
   ollama serve
   ```
4. **Configure PayScope**: Add to your `.env` file:
   ```env
   LLM_PROVIDER=local
   LLM_LOCAL_PROVIDER=ollama
   LLM_LOCAL_MODEL=llama3.1:8b
   ```

### Option 2: Hugging Face Inference API (Free Tier)

1. **Get HF API Token**: https://huggingface.co/settings/tokens
2. **Configure PayScope**: Add to your `.env` file:
   ```env
   LLM_PROVIDER=hf
   HF_API_TOKEN=your_token_here
   ```

### Option 3: Auto-detect (HF with local fallback)

```env
LLM_PROVIDER=auto
HF_API_TOKEN=your_token_here  # Optional, falls back to local if not set
LLM_LOCAL_PROVIDER=ollama
```

## How It Works

The system automatically detects which LLM provider to use:

1. **Priority Order**:
   - If `LLM_PROVIDER=openai` or OpenAI credentials are set → Uses OpenAI-compatible API
   - If `LLM_PROVIDER=local` → Uses local Ollama/vLLM
   - If `LLM_PROVIDER=hf` → Uses Hugging Face Inference API
   - If `LLM_PROVIDER=auto` → Tries HF first, falls back to local

2. **Integration Points**:
   - **Document Mapping**: LLM-based field mapping for CSV/Excel normalization
   - **Intent Classification**: Query intent detection for RAG engine
   - **Agent Reasoning**: AI agent decision-making

3. **Backward Compatibility**:
   - Existing OpenAI API keys still work
   - System falls back gracefully if free LLM is unavailable
   - No code changes required - just environment variables

## Testing

Test the integration:

```bash
# Test with local Ollama
python scripts/test_free_llm.py
```

Or test via the API:

```bash
# Upload a report and let the system use LLaMA for mapping
curl -X POST http://localhost:8000/api/upload \
  -H "X-Bank-Id: your-bank-id" \
  -F "file=@sample_report.csv"
```

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Provider type: `openai`, `hf`, `local`, `auto` | `openai` |
| `HF_API_TOKEN` | Hugging Face API token | - |
| `LLM_LOCAL_PROVIDER` | Local provider: `ollama` or `vllm` | `ollama` |
| `LLM_LOCAL_BASE_URL` | Local server URL | `http://localhost:11434` (Ollama) |
| `LLM_LOCAL_MODEL` | Model name | `llama3.1:8b` (Ollama) |

## Troubleshooting

### Ollama not found
- Ensure Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`
- Verify port 11434 is accessible

### HF API errors
- Check token is valid and has inference access
- Free tier has rate limits - system will fall back to local if available

### Model not responding
- Check logs for specific error messages
- Verify model name matches downloaded model
- Try testing directly: `ollama run llama3.1:8b`

## Performance Notes

- **Local Ollama**: Best for development, no API costs, but requires local resources
- **HF Inference API**: Free tier has rate limits, good for testing
- **OpenAI API**: Best performance but requires paid API key

All providers are OpenAI-compatible, so switching is just a config change!



