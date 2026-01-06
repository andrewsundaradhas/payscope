# Quick Setup - Your Credentials

## ✅ What You Have

1. **Pinecone API Key**: `pcsk_2VM8i3_SW9VaYh6tMVXa6msEsZjNLnWn3tYiRdH2pCxKDjUsd2ArrJosHmwYu3yKYjJY4`
2. **Neo4j AuraDB Free**: Connection URI: `neo4j+s://a3c08613.databases.neo4j.io`

## 🚀 Step-by-Step Setup

### Step 1: Update .env File

Open your `.env` file and add/update these lines:

```env
# Pinecone
PINECONE_API_KEY=pcsk_2VM8i3_SW9VaYh6tMVXa6msEsZjNLnWn3tYiRdH2pCxKDjUsd2ArrJosHmwYu3yKYjJY4
PINECONE_INDEX_NAME=payscope-index
PINECONE_NAMESPACE=payscope

# Neo4j AuraDB (get password from Neo4j dashboard)
NEO4J_URI=neo4j+s://a3c08613.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password-here
```

**Important:** 
- Get your Neo4j password from the Neo4j AuraDB dashboard (it's shown when you create the instance, usually starts with something like `password123...`)
- Username for AuraDB is typically `neo4j`

### Step 2: Install Pinecone Client

```powershell
pip install pinecone-client
```

Or if using Poetry (recommended for this project):
```powershell
poetry add pinecone-client
```

### Step 3: Create Pinecone Index

Run the setup script:

```powershell
python scripts/create-pinecone-index.py
```

This will create an index named `payscope-index` with:
- **Dimensions**: 768 (required for the embedding model)
- **Metric**: cosine
- **Type**: Serverless (free tier)

### Step 4: Verify Setup

```powershell
# Check all dependencies
python scripts/check-dependencies.py
```

### Step 5: Start Services

Since you're using Neo4j AuraDB (cloud), you don't need to start Neo4j locally. Just start the other services:

```powershell
docker compose up -d postgres redis minio
```

Or start all services (excluding Neo4j since you're using cloud):
```powershell
docker compose up -d
```

### Step 6: Run Migrations

```powershell
.\scripts\run-migrations.ps1
```

## 🎯 Quick Commands Summary

```powershell
# 1. Install Pinecone
pip install pinecone-client

# 2. Add credentials to .env (edit manually)

# 3. Create Pinecone index
python scripts/create-pinecone-index.py

# 4. Verify
python scripts/check-dependencies.py

# 5. Start services
docker compose up -d

# 6. Run migrations
.\scripts\run-migrations.ps1
```

## 📝 Important Notes

1. **Neo4j AuraDB**: You're using the cloud version, so:
   - Don't worry about local Neo4j Docker container
   - Make sure you have the password from your AuraDB dashboard
   - The connection uses `neo4j+s://` (secure connection) which is perfect

2. **Pinecone Index**: 
   - The script creates index with 768 dimensions (required)
   - Uses Serverless (free tier compatible)
   - Index name: `payscope-index`

3. **LLM API Key**: Optional - add if you want AI features, otherwise the system uses rule-based fallbacks

## ✅ You're Ready!

Once you complete these steps, PayScope will be fully configured and ready to use!



