# Quick Setup - Your Credentials

## ✅ What You Have

Based on your setup:

1. **Pinecone API Key**: `pcsk_2VM8i3_SW9VaYh6tMVXa6msEsZjNLnWn3tYiRdH2pCxKDjUsd2ArrJosHmwYu3yKYjJY4`
2. **Neo4j AuraDB Free**: `neo4j+s://a3c08613.databases.neo4j.io`

## 📝 Step 1: Configure .env File

Edit your `.env` file (or create from `env/local.env.example`):

```env
# Pinecone (REQUIRED)
PINECONE_API_KEY=pcsk_2VM8i3_SW9VaYh6tMVXa6msEsZjNLnWn3tYiRdH2pCxKDjUsd2ArrJosHmwYu3yKYjJY4
PINECONE_INDEX_NAME=payscope-index
PINECONE_NAMESPACE=payscope

# Neo4j AuraDB (REQUIRED - get password from Neo4j dashboard)
NEO4J_URI=neo4j+s://a3c08613.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password-here

# LLM (OPTIONAL - for AI features)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-key-here
LLM_MODEL=gpt-4o-mini
```

**Important:** 
- Get your Neo4j password from the Neo4j AuraDB dashboard (it's shown when you create the instance)
- The username is usually `neo4j` for AuraDB

## 📝 Step 2: Create Pinecone Index

Run this command to create the index:

```powershell
python scripts/create-pinecone-index.py
```

Or manually create it:

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="pcsk_2VM8i3_SW9VaYh6tMVXa6msEsZjNLnWn3tYiRdH2pCxKDjUsd2ArrJosHmwYu3yKYjJY4")

pc.create_index(
    name="payscope-index",
    dimension=768,  # Required: matches embedding model
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

## 📝 Step 3: Verify Setup

```powershell
# Check dependencies
python scripts/check-dependencies.py

# Start services (Postgres, Redis, MinIO will run locally)
docker compose up -d

# Run migrations
.\scripts\run-migrations.ps1
```

## 🔍 Neo4j AuraDB Notes

Since you're using **Neo4j AuraDB** (cloud), NOT local Docker:

1. **Don't start Neo4j in docker-compose** - you're using cloud version
2. **Connection URI**: `neo4j+s://a3c08613.databases.neo4j.io` (already have this)
3. **Username**: Usually `neo4j`
4. **Password**: Get from your AuraDB dashboard (shown when instance is created)

The connection uses `neo4j+s://` (secure) instead of `bolt://` (local), which is perfect!

## ✅ You're Ready!

Once you:
1. ✅ Add Pinecone API key to `.env`
2. ✅ Add Neo4j credentials to `.env`
3. ✅ Create Pinecone index
4. ✅ Start local services (postgres, redis, minio)

You can start using PayScope!



