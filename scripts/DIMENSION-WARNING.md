# ⚠️ Pinecone Index Dimension Mismatch

## Issue

Your Pinecone index `llama-text-embed-v2-index` has **512 dimensions**, but PayScope uses the embedding model `BAAI/bge-base-en-v1.5` which produces **768 dimensions**.

This mismatch will cause errors when trying to upsert vectors.

## Solutions

### Option 1: Create a New Index with 768 Dimensions (Recommended)

Create a new index specifically for PayScope:

```powershell
# Update .env with new index name
# Edit .env and change:
# PINECONE_INDEX_NAME=payscope-index

# Then create the index
python scripts/create-pinecone-index.py
```

The script will create an index with:
- Name: `payscope-index` (or whatever you set)
- Dimensions: **768** (matches BAAI/bge-base-en-v1.5)
- Metric: cosine
- Type: Serverless

### Option 2: Use Your Existing Index (Requires Code Changes)

If you want to use your existing 512-dimension index, you would need to:

1. **Change the embedding model** to one that produces 512 dimensions
2. **Update the code** to use the new model

**Not recommended** - This requires modifying the codebase.

### Option 3: Create Index Manually

If the script doesn't work, create it manually via Pinecone console:

1. Go to https://app.pinecone.io/
2. Create new index
3. Settings:
   - Name: `payscope-index`
   - Dimensions: **768**
   - Metric: Cosine
   - Type: Serverless (or Pod-based if you prefer)

## Current Configuration

- **Your Index:** `llama-text-embed-v2-index` (512 dims)
- **PayScope Model:** `BAAI/bge-base-en-v1.5` (768 dims)
- **Status:** ❌ Incompatible

## Recommendation

**Create a new index** with 768 dimensions for PayScope. You can keep your existing index for other projects.



