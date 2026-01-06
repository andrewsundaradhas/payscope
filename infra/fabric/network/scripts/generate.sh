#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p channel-artifacts

if ! command -v cryptogen >/dev/null 2>&1; then
  echo "cryptogen not found. Use Fabric binaries or run via a fabric-tools container." >&2
  exit 1
fi
if ! command -v configtxgen >/dev/null 2>&1; then
  echo "configtxgen not found. Use Fabric binaries or run via a fabric-tools container." >&2
  exit 1
fi

rm -rf crypto-config channel-artifacts/*

cryptogen generate --config=crypto-config.yaml

export FABRIC_CFG_PATH="$ROOT_DIR"

configtxgen -profile PayScopeOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block
configtxgen -profile PayScopeChannel -outputCreateChannelTx ./channel-artifacts/payscopechannel.tx -channelID payscopechannel

echo "Generated crypto material and channel artifacts."




