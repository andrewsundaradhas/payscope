# Installing Docker Desktop on Windows

## Quick Installation Guide

### Option 1: Using Winget (Recommended - Fastest)

Open PowerShell **as Administrator** and run:

```powershell
winget install Docker.DockerDesktop
```

### Option 2: Manual Download

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - Save the installer (`Docker Desktop Installer.exe`)

2. **Run the Installer:**
   - Double-click `Docker Desktop Installer.exe`
   - Follow the installation wizard
   - **Important:** Make sure "Use WSL 2 instead of Hyper-V" is checked (if available)

3. **Restart Computer:**
   - Docker Desktop will prompt you to restart
   - Complete the restart

4. **Start Docker Desktop:**
   - After restart, Docker Desktop should start automatically
   - If not, start it from Start Menu: "Docker Desktop"
   - Wait for Docker to fully start (whale icon in system tray)

5. **Verify Installation:**
   ```powershell
   docker --version
   docker compose version
   ```

## After Installation

Once Docker is installed, you can continue with:

```powershell
# Start PayScope services
cd infra
docker compose -f docker-compose.local.yml up -d

# Verify services are running
docker compose -f docker-compose.local.yml ps

# Check dependency status
cd ..
python scripts/check-dependencies.py
```

## Troubleshooting

### "Docker Desktop is not running"
- Open Docker Desktop from Start Menu
- Wait for it to fully start (whale icon should be steady, not animated)

### "WSL 2 installation is incomplete"
- Download WSL 2 update: https://aka.ms/wsl2kernel
- Install the update
- Restart computer

### Port conflicts
- Close applications using ports 5432, 6379, 7474, 7687, 9000, 9001
- Or modify ports in `docker-compose.local.yml`

## Next Steps After Docker Installation

1. **Verify Docker is running:**
   ```powershell
   docker ps
   ```

2. **Start PayScope services:**
   ```powershell
   cd infra
   docker compose -f docker-compose.local.yml up -d
   ```

3. **Create MinIO bucket:**
   - Open: http://localhost:9001
   - Login: `payscope` / `payscope-secret`
   - Create bucket: `payscope-raw`
   - Enable encryption

4. **Verify all dependencies:**
   ```powershell
   cd ..
   python scripts/check-dependencies.py
   ```



