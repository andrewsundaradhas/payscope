# Hyperledger Fabric — Audit Ledger (Phase 9)

This folder provides a **permissioned** Hyperledger Fabric setup for immutable audit logging.

## What goes on-chain

**Hashed artifacts only** (no raw report content, no PII, no raw financial data):

- Input hashes (report files, parsed docs, canonical facts)
- Agent decisions (agent_id/task_id/decision hash)
- Forecast/simulation outputs (model_id/scenario_id/output hash)

Each chain write must store the schema:

```json
{
  "event_id": "uuid",
  "event_type": "INGEST | AGENT_DECISION | FORECAST",
  "artifact_hash": "sha256",
  "schema_version": "vX",
  "timestamp": "UTC"
}
```

## Chaincode language note (blocking)

Fabric chaincode is implemented in **Go** for schema enforcement and idempotency (blockchain/infra scope).

## Deliverables in this folder

- Network scaffolding (compose/config): `infra/fabric/network/`
- Audit chaincode (Go): `infra/fabric-chaincode/auditlog/`


