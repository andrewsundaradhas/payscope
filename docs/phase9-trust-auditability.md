## Phase 9 — Trust & Auditability

This phase adds cryptographic verification, explainability storage, and a permissioned immutable ledger (Hyperledger Fabric).

### 9.1 Immutable ledger (Fabric)

On-chain: **hashes only**.
Off-chain: prompts (redacted where required), decision traces, model versions, schema versions, confidence values.

Ledger entry schema (enforced by chaincode):
```json
{
  "event_id": "uuid",
  "event_type": "INGEST | AGENT_DECISION | FORECAST",
  "artifact_hash": "sha256",
  "schema_version": "vX",
  "timestamp": "UTC"
}
```

Idempotency rule:
- event_id is the ledger key
- if the same event_id is written again:
  - allow if payload hash matches
  - reject if payload differs

### 9.2 Explainability & traceability (off-chain)

DDL:
- `infra/postgres/002_explainability_audit.sql`

Stored off-chain:
- prompt versions (redacted text + sha256)
- model versions (sha256)
- schema versions (sha256)
- AI outputs: input hash, output hash, confidences, and ledger references
- agent decision traces with ledger references

### Hashing & signing utilities (Python 3.11)

- Deterministic hashing:
  - `processing/src/payscope_processing/audit/hashing.py`
  - canonical JSON serialization (sorted keys, compact separators)
  - sha256 for bytes/files/objects
- Signing (Ed25519):
  - `processing/src/payscope_processing/audit/signing.py`

### End-to-end audit verification flow (verifiable)

Given an AI output (canonical facts / agent decision / forecast):
1) Compute `input_hash_sha256` and `output_hash_sha256` deterministically.
2) Write a Fabric ledger event with `artifact_hash=output_hash_sha256`.
3) Persist off-chain record referencing:
   - `model_version`, `prompt_version`, `schema_version`
   - `ledger_event_id`, `ledger_tx_id`
4) Auditor verifies:
   - recompute hash from the supplied artifact
   - compare to on-chain `artifact_hash`
   - validate ledger tx is in Fabric history and schema-valid
   - validate off-chain records reference the same ledger_event_id and version objects

### Remaining blocking item

Fabric chaincode implemented in Go at `infra/fabric-chaincode/auditlog/` and network scaffold at `infra/fabric/network/`.


