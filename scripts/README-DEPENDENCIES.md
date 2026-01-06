# External Dependencies Check

Before starting PayScope services, verify all external dependencies are configured and accessible.

## Quick Check

Run the dependency checker:

```powershell
python scripts/check-dependencies.py
```

Or use PowerShell version:

```powershell
.\scripts\check-dependencies.ps1
```

## Dependencies Required

### 1. Pinecone Index

**Requirement:** Index must be created before starting services.

**Configuration (in .env):**
```
PINECONE_API_KEY=your-api-key
PINECONE_INDEX_NAME=your-index-name
```

**To create index:**
```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your-api-key")
pc.create_index(
    name="your-index-name",
    dimension=768,  # Match your embedding model dimension
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

**Check:** Script verifies index exists and is accessible.

---

### 2. Neo4j Database

**Requirement:** Neo4j must be running and reachable.

**Configuration (in .env):**
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

**For local Docker:**
```yaml
neo4j:
  image: neo4j:5
  environment:
    NEO4J_AUTH: neo4j/your-password
  ports:
    - "7474:7474"
    - "7687:7687"
```

**Check:** Script verifies connection and authentication.

---

### 3. MinIO/S3 Object Storage

**Requirement:** Bucket must exist with Server-Side Encryption (SSE) enabled.

**Configuration (in .env):**
```
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minio
S3_SECRET_ACCESS_KEY=minio123
S3_BUCKET=payscope-raw
```

**To create bucket with SSE (MinIO Console):**
1. Open MinIO Console: http://localhost:9001
2. Login with access key and secret
3. Create bucket: `payscope-raw`
4. Enable encryption (Settings → Encryption → Enable)

**Or via AWS CLI:**
```bash
aws --endpoint-url http://localhost:9000 s3 mb s3://payscope-raw
aws --endpoint-url http://localhost:9000 s3api put-bucket-encryption \
  --bucket payscope-raw \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

**Check:** Script verifies bucket exists and SSE is enabled.

---

### 4. Docker Port Availability

**Requirement:** Required ports must not be in use.

**Ports checked:**
- `5432` - PostgreSQL/TimescaleDB
- `6379` - Redis
- `7687` - Neo4j (bolt)
- `7474` - Neo4j Browser
- `9000` - MinIO API
- `9001` - MinIO Console
- `8000` - API service
- `8080` - Ingestion service

**Check:** Script verifies ports are available (not in use).

**To check manually:**
```powershell
# Windows
netstat -an | findstr :5432

# Or use PowerShell
Test-NetConnection -ComputerName localhost -Port 5432
```

---

## Manual Verification Steps

If the automated check fails, verify manually:

### Pinecone
```python
from pinecone import Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
indexes = pc.list_indexes()
print([idx.name for idx in indexes])
```

### Neo4j
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)
with driver.session() as session:
    result = session.run("RETURN 1")
    print(result.single())
driver.close()
```

### MinIO/S3
```python
import boto3
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY")
)
s3.head_bucket(Bucket=os.getenv("S3_BUCKET"))
```

### Docker Ports
```powershell
# Check all ports
@(5432, 6379, 7687, 7474, 9000, 9001, 8000, 8080) | ForEach-Object {
    $result = Test-NetConnection -ComputerName localhost -Port $_ -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "Port $_ is in use"
    }
}
```

---

## Troubleshooting

### Pinecone: "Index not found"
- Create the index first (see above)
- Verify `PINECONE_INDEX_NAME` matches the actual index name
- Check API key has access to the index

### Neo4j: "Connection refused"
- Start Neo4j: `docker compose up -d neo4j`
- Verify URI format: `bolt://host:port` or `neo4j://host:port`
- Check firewall/network settings

### MinIO/S3: "Bucket does not exist"
- Create bucket in MinIO Console or via API
- Verify bucket name matches `S3_BUCKET` in .env
- Check credentials have permission to access bucket

### MinIO/S3: "SSE not enabled"
- Enable encryption in MinIO Console (Settings → Encryption)
- Or configure via S3 API (see above)

### Docker: "Port already in use"
- Stop the service using the port
- Or change the port in docker-compose.yml
- Check with: `netstat -an | findstr :PORT`

---

## Next Steps

Once all dependencies pass:

1. **Run migrations:**
   ```powershell
   .\scripts\run-migrations.ps1
   ```

2. **Start services:**
   ```powershell
   docker compose up -d
   ```

3. **Validate setup:**
   ```powershell
   .\scripts\validate-setup.ps1
   ```



