# PayScope - Credentials & Setup Guide

## ✅ Product Status: **COMPLETE & PRODUCTION READY**

The PayScope backend is **fully implemented** and ready to deploy. You just need to configure external API credentials.

---

## 🔑 Required Credentials

### **1. Pinecone API Key** (REQUIRED for vector search)

**What it's for:** Stores document embeddings for semantic search

**How to get it:**
1. Go to https://www.pinecone.io/
2. Sign up (free tier available)
3. Navigate to **API Keys** section
4. Copy your API key (starts with `pc-` or `pcsk-`)

**Add to `.env` file:**
```env
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=payscope-index
```

**After adding, create the index:**
```powershell
python scripts/create-pinecone-index.py
```

---

### **2. LLM API Key** (OPTIONAL - for AI features)

**What it's for:** Powers intent classification, RAG queries, and agent reasoning

**Options:**
- **OpenAI** (recommended): https://platform.openai.com/api-keys
- **OpenAI-compatible** (e.g., TGI, Ollama): Any OpenAI-compatible endpoint

**Add to `.env` file:**
```env
# Option 1: OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-openai-key-here
LLM_MODEL=gpt-4o-mini

# Option 2: Self-hosted (e.g., TGI)
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=not-needed-for-local
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**Note:** If not configured, the system will use rule-based fallbacks (less intelligent but still functional).

---

### **3. Neo4j Password** (REQUIRED for graph features)

**What it's for:** Stores relationship graphs between transactions, merchants, issuers

**How to set it:**
1. Choose any secure password
2. Add to `.env` file:
```env
NEO4J_PASSWORD=your-secure-password-here
```

**Note:** This is just a password you choose - no external account needed. Neo4j runs locally in Docker.

---

## 🚫 NOT Required (Already Configured)

These are **already set up** and don't need external credentials:

- ✅ **PostgreSQL/TimescaleDB** - Runs in Docker (no credentials needed)
- ✅ **Redis** - Runs in Docker (no credentials needed)
- ✅ **MinIO/S3** - Runs in Docker (default credentials: `payscope/payscope-secret`)
- ✅ **JWT Keys** - Auto-generated (see `scripts/generate-jwt-keys.py`)

---

## 📋 Quick Setup Checklist

### Step 1: Create `.env` file
```powershell
# Copy the example
Copy-Item env\local.env.example .env
```

### Step 2: Add Required Credentials
Edit `.env` and add:
```env
# Pinecone (REQUIRED)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=payscope-index

# Neo4j (REQUIRED - choose any password)
NEO4J_PASSWORD=your-secure-password

# LLM (OPTIONAL - for AI features)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-key
LLM_MODEL=gpt-4o-mini
```

### Step 3: Create Pinecone Index
```powershell
python scripts/create-pinecone-index.py
```

### Step 4: Generate JWT Keys (if not done)
```powershell
python scripts/generate-jwt-keys.py
```

### Step 5: Start Services
```powershell
docker compose up -d
```

### Step 6: Run Migrations
```powershell
.\scripts\run-migrations.ps1
```

### Step 7: Verify Setup
```powershell
python scripts/check-dependencies.py
```

---

## 🎯 Minimum Setup (Testing Without AI)

If you want to test **without AI features**, you only need:

1. **Pinecone API Key** (for vector search)
2. **Neo4j Password** (for graph storage)

The system will work with rule-based fallbacks for intent classification and queries.

---

## 💰 Cost Estimates

### Free Tier Available:
- **Pinecone**: Free tier includes 1 index, 100K vectors
- **Neo4j**: Free (runs locally)
- **PostgreSQL/Redis/MinIO**: Free (runs locally)

### Paid (Optional):
- **OpenAI API**: ~$0.15 per 1M tokens (gpt-4o-mini)
- **Pinecone**: Pay-as-you-go after free tier

---

## 🔍 Verify Your Setup

After adding credentials, verify everything works:

```powershell
# Check all dependencies
python scripts/check-dependencies.py

# Check health endpoints
curl http://localhost:8000/health/ready

# Check metrics
curl http://localhost:8000/metrics
```

---

## 📚 More Help

- **Full setup guide**: `scripts/QUICK-START.md`
- **Dependencies guide**: `scripts/README-DEPENDENCIES.md`
- **Deployment checklist**: `DEPLOYMENT_CHECKLIST.md`

---

## ✅ Summary

**Product Status:** ✅ **COMPLETE**

**What you need:**
1. ✅ Pinecone API key (get from pinecone.io)
2. ✅ Neo4j password (choose any password)
3. ⚠️ LLM API key (optional - for AI features)

**Everything else:** Already configured and ready to go!



