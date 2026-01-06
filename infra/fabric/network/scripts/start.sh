#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose -f docker-compose.yaml up -d
echo "Fabric network containers started."
echo "Next: use the cli container to create/join channel and deploy chaincode."




