# Quick Configuration Guide

Since the interactive script requires manual input, use one of these methods:

## Method 1: Command-Line Parameters (Recommended)

Run the script with your values:

```powershell
.\scripts\configure-dependencies.ps1 `
  -PineconeApiKey "your-api-key-here" `
  -PineconeIndexName "payscope-index" `
  -Neo4jPassword "your-secure-password"
```

**Example:**
```powershell
.\scripts\configure-dependencies.ps1 `
  -PineconeApiKey "pc-abc123xyz" `
  -PineconeIndexName "payscope-index" `
  -Neo4jPassword "MySecurePass123!"
```

## Method 2: Manual Edit

Edit the `.env` file directly and add:

```env
# Pinecone
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=payscope-index

# Neo4j
NEO4J_PASSWORD=your-secure-password-here
```

## Method 3: Environment Variables

Set environment variables, then run the script:

```powershell
$env:PINECONE_API_KEY = "your-api-key"
$env:PINECONE_INDEX_NAME = "payscope-index"
$env:NEO4J_PASSWORD = "your-password"

# Then edit .env manually or use a script
```

## After Configuration

1. **Create Pinecone Index:**
   ```powershell
   python scripts/create-pinecone-index.py
   ```

2. **Start Services:**
   ```powershell
   cd infra
   docker compose -f docker-compose.local.yml up -d
   ```

3. **Verify:**
   ```powershell
   python scripts/check-dependencies.py
   ```

## Getting Your Pinecone API Key

1. Go to https://www.pinecone.io/
2. Sign up or log in
3. Navigate to API Keys
4. Copy your API key

## Getting Started Without Pinecone (Testing)

If you want to test without Pinecone first, you can:
- Skip Pinecone configuration (services will fail on vector operations)
- Or use a mock/test Pinecone setup

For Neo4j, you can use any secure password you want.



