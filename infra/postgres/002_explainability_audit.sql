-- Phase 9.2 — Explainability & traceability storage (off-chain)
-- Store prompts (redacted where required), model inputs/outputs (hashed), consensus traces, and ledger references.
-- No raw PII/financial payloads are required here; store hashes + pointers.

BEGIN;

CREATE TABLE IF NOT EXISTS prompt_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_name TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  prompt_hash_sha256 CHAR(64) NOT NULL,
  prompt_redacted TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (prompt_name, prompt_version)
);

CREATE TABLE IF NOT EXISTS model_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  model_hash_sha256 CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (model_name, model_version)
);

CREATE TABLE IF NOT EXISTS schema_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schema_name TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  schema_hash_sha256 CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (schema_name, schema_version)
);

CREATE TABLE IF NOT EXISTS ai_outputs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  output_type TEXT NOT NULL, -- "canonical_facts" | "agent_decision" | "forecast" | "rag_response"
  output_hash_sha256 CHAR(64) NOT NULL,

  model_version_id UUID NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
  prompt_version_id UUID NULL REFERENCES prompt_versions(id) ON DELETE RESTRICT,
  schema_version_id UUID NOT NULL REFERENCES schema_versions(id) ON DELETE RESTRICT,

  ledger_event_id UUID NOT NULL,
  ledger_tx_id TEXT NOT NULL,

  -- hashed inputs for audit replay (no raw data)
  input_hash_sha256 CHAR(64) NOT NULL,

  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (output_hash_sha256, schema_version_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_outputs_ledger_event
  ON ai_outputs (ledger_event_id);

CREATE TABLE IF NOT EXISTS agent_decision_traces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  decision_hash_sha256 CHAR(64) NOT NULL,
  decision_rationale TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  ledger_event_id UUID NOT NULL,
  ledger_tx_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (agent_id, task_id, decision_hash_sha256)
);

COMMIT;




