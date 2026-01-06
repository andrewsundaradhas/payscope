# Next Steps - Start Services

## ✅ Completed Setup

- ✅ Pinecone index created (`payscope-index`, 768 dimensions)
- ✅ Docker Compose files created
- ✅ Configuration files ready (.env)
- ✅ Neo4j password configured

## 🚀 Starting Services

### Option 1: Using Helper Script (Recommended)

```powershell
.\scripts\start-services.ps1
```

This script will:
- Verify Docker is installed and running
- Check for .env file
- Start all services in detached mode
- Show service status

### Option 2: Manual Docker Compose

```powershell
# Build and start all services
docker compose up -d --build

# Or start without building
docker compose up -d

# View service status
docker compose ps

# View logs
docker compose logs -f
```

## 📋 Post-Startup Tasks

### 1. Create MinIO Bucket

After MinIO starts (port 9001):

1. Open: http://localhost:9001
2. Login:
   - Username: `payscope`
   - Password: `payscope-secret`
3. Create bucket:
   - Click "Create Bucket"
   - Name: `payscope-raw`
   - Enable encryption (SSE)

### 2. Run Database Migrations

```powershell
# Set DATABASE_URL
$env:DATABASE_URL = "postgresql://payscope:payscope@localhost:5432/payscope"

# Run migrations
.\scripts\run-migrations.ps1
```

### 3. Verify All Dependencies

```powershell
python scripts/check-dependencies.py
```

Expected output:
```
[OK] Pinecone Index: Index 'payscope-index' exists (dimensions: 768)
[OK] Neo4j Connection: Connected to Neo4j at bolt://localhost:7687
[OK] MinIO/S3 Bucket: Bucket 'payscope-raw' exists with SSE
[OK] Docker Ports: All required ports are available
```

## 🔍 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| Ingestion | http://localhost:8080 | - |
| MinIO Console | http://localhost:9001 | payscope / payscope-secret |
| Neo4j Browser | http://localhost:7474 | neo4j / (your password) |

## 🛠️ Troubleshooting

### Services won't start

1. **Check Docker is running:**
   ```powershell
   docker ps
   ```

2. **Check port conflicts:**
   ```powershell
   netstat -an | findstr "5432 6379 7474 7687 9000 9001 8000 8080"
   ```

3. **View service logs:**
   ```powershell
   docker compose logs [service-name]
   ```

### Build errors

```powershell
# Rebuild specific service
docker compose build [service-name]

# Rebuild all services
docker compose build --no-cache
```

### Database connection issues

- Verify PostgreSQL is running: `docker compose ps postgres`
- Check logs: `docker compose logs postgres`
- Verify credentials match in .env

### Neo4j connection issues

- Verify Neo4j is running: `docker compose ps neo4j`
- Check password matches in .env and docker-compose
- Wait for Neo4j to fully start (takes ~30 seconds)

## 📝 Important Notes

1. **MinIO Credentials:**
   - Docker Compose and .env both use: `payscope/payscope-secret`
   - Credentials are now consistent across all configuration files

2. **First Start:**
   - Services may take 30-60 seconds to fully initialize
   - Neo4j requires initial password change on first start (already configured)
   - MinIO bucket must be created manually via console

3. **Environment Variables:**
   - All application services (API, ingestion, worker) load from `.env`
   - Infrastructure services (postgres, redis, minio, neo4j) use docker-compose environment variables

## ✅ Verification Checklist

- [ ] All services are running (`docker compose ps`)
- [ ] MinIO bucket `payscope-raw` created and encrypted
- [ ] Database migrations completed
- [ ] All dependencies verified (`python scripts/check-dependencies.py`)
- [ ] API accessible at http://localhost:8000/docs
- [ ] Ingestion service accessible at http://localhost:8080

## 🎯 Ready for Testing

Once all checks pass, you can:

1. **Upload test data:**
   ```powershell
   curl -X POST http://localhost:8080/upload `
     -H "X-Bank-Id: 00000000-0000-0000-0000-000000000001" `
     -F "files=@test-report.pdf"
   ```

2. **Check processing logs:**
   ```powershell
   docker compose logs -f worker
   ```

3. **Query the API:**
   - Visit http://localhost:8000/docs for interactive API documentation

