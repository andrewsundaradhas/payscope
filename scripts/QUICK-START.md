# Quick Start Guide - Configure Dependencies

Follow these steps to configure Pinecone and Neo4j, then start services.

## Step 1: Configure Pinecone

### 1.1 Get Pinecone API Key

1. Go to https://www.pinecone.io/
2. Sign up or log in
3. Go to API Keys section
4. Copy your API key

### 1.2 Add to .env File

**Option A: Interactive (Recommended)**
```powershell
.\scripts\setup-env-dependencies.ps1
```

**Option B: Manual**
Edit `.env` file and add:
```env
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=payscope-index
```

### 1.3 Create Pinecone Index

After adding the API key, create the index:
```powershell
python scripts/create-pinecone-index.py
```

This will create an index with:
- Name: `payscope-index` (or whatever you set)
- Dimensions: 768 (for BAAI/bge-base-en-v1.5 embedding model)
- Metric: cosine
- Type: Serverless (free tier)

---

## Step 2: Configure Neo4j

### 2.1 Add Password to .env

**Option A: Interactive**
```powershell
.\scripts\setup-env-dependencies.ps1
```

**Option B: Manual**
Edit `.env` file and add:
```env
NEO4J_PASSWORD=your-secure-password-here
```

**Note:** Choose a strong password. This will be used by Neo4j when it starts.

### 2.2 Update docker-compose.yml (if needed)

If your `docker-compose.yml` doesn't have Neo4j, add it. The service should look like:
```yaml
neo4j:
  image: neo4j:5
  environment:
    NEO4J_AUTH: neo4j/your-password-here
  ports:
    - "7474:7474"  # Browser
    - "7687:7687"  # Bolt
  volumes:
    - neo4j_data:/data
```

Make sure the password matches what you set in `.env`.

---

## Step 3: Start Services

### 3.1 Start Docker Services

Navigate to the directory with your `docker-compose.yml` file (likely `infra/`):
```powershell
cd infra
docker compose -f docker-compose.local.yml up -d
```

Or if you have a `docker-compose.yml` in the root:
```powershell
docker compose up -d
```

This will start:
- PostgreSQL/TimescaleDB
- Redis
- MinIO
- Neo4j (if configured)
- Ingestion service
- Processing service

### 3.2 Wait for Services to Start

Give services a few seconds to initialize:
```powershell
# Check status
docker compose ps

# Check logs
docker compose logs -f
```

---

## Step 4: Create MinIO Bucket

After MinIO starts:

1. **Open MinIO Console:** http://localhost:9001
2. **Login:**
   - Username: `payscope` (from docker-compose)
   - Password: `payscope-secret` (from docker-compose)
3. **Create Bucket:**
   - Click "Create Bucket"
   - Name: `payscope-raw`
   - Enable "Versioning" (optional)
   - Click "Create Bucket"
4. **Enable Encryption (SSE):**
   - Click on the bucket
   - Go to "Configuration" → "Encryption"
   - Enable encryption
   - Save

**Or use AWS CLI:**
```powershell
# Install AWS CLI first, then:
aws --endpoint-url http://localhost:9000 configure set aws_access_key_id payscope
aws --endpoint-url http://localhost:9000 configure set aws_secret_access_key payscope-secret

aws --endpoint-url http://localhost:9000 s3 mb s3://payscope-raw
```

---

## Step 5: Verify Dependencies

Run the dependency checker:
```powershell
python scripts/check-dependencies.py
```

You should see:
```
[OK] Pinecone Index: Index 'payscope-index' exists
[OK] Neo4j Connection: Connected to Neo4j at bolt://localhost:7687
[OK] MinIO/S3 Bucket: Bucket 'payscope-raw' exists with SSE
[OK] Docker Ports: All required ports are available
```

If any checks fail, review the error messages and fix the issues.

---

## Step 6: Run Database Migrations

After all services are running:
```powershell
# Set DATABASE_URL (if not already set)
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"

# Run migrations
.\scripts\run-migrations.ps1
```

---

## Troubleshooting

### Pinecone: "API key invalid"
- Verify your API key is correct
- Check you're using the right environment (free tier vs paid)

### Neo4j: "Connection refused"
- Make sure Neo4j service is running: `docker compose ps neo4j`
- Check logs: `docker compose logs neo4j`
- Verify password matches in `.env` and `docker-compose.yml`

### MinIO: "Cannot connect"
- Make sure MinIO is running: `docker compose ps minio`
- Wait a few seconds after starting (MinIO needs time to initialize)
- Check logs: `docker compose logs minio`

### Port conflicts
- Check what's using the port: `netstat -an | findstr :PORT`
- Stop conflicting services or change ports in docker-compose.yml

---

## Next Steps

Once all dependencies pass:

1. **Validate full setup:**
   ```powershell
   .\scripts\validate-setup.ps1
   ```

2. **Upload test data:**
   ```powershell
   # Example upload
   curl -X POST http://localhost:8080/upload `
     -H "X-Bank-Id: 00000000-0000-0000-0000-000000000001" `
     -F "files=@test-report.pdf"
   ```

3. **Check processing status:**
   ```powershell
   docker compose logs -f processing
   ```

---

## Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| MinIO API | http://localhost:9000 | payscope / payscope-secret |
| MinIO Console | http://localhost:9001 | payscope / payscope-secret |
| Neo4j Browser | http://localhost:7474 | neo4j / (your password) |
| API Docs | http://localhost:8000/docs | - |
| Ingestion API | http://localhost:8080 | - |



