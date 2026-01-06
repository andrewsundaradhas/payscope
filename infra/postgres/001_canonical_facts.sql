-- Phase 4.1 — PostgreSQL canonical facts store
-- Purpose: authoritative normalized payment facts with strong consistency.
-- Deterministic + idempotent upserts are enabled via UNIQUE constraints.

BEGIN;

-- Extensions for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Canonical enums
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lifecycle_stage') THEN
    CREATE TYPE lifecycle_stage AS ENUM ('AUTH', 'CLEARING', 'SETTLEMENT');
  END IF;
END $$;

-- Reports (authoritative ingestion batches)
CREATE TABLE IF NOT EXISTS reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Upstream identifier (Phase 3 ReportFact.report_id)
  report_id UUID NOT NULL,
  bank_id UUID NOT NULL,

  report_type TEXT NOT NULL,
  ingestion_time TIMESTAMPTZ NOT NULL,
  source_network TEXT NOT NULL,
  record_count INTEGER NOT NULL CHECK (record_count >= 0),

  schema_version TEXT NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enforce idempotent inserts per canonical report id + schema version.
CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_report_id_schema
  ON reports (bank_id, report_id, schema_version);

CREATE INDEX IF NOT EXISTS idx_reports_ingestion_time
  ON reports (bank_id, ingestion_time);

-- Merchants
CREATE TABLE IF NOT EXISTS merchants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Canonical merchant identifier (Phase 3 TransactionFact.merchant_id)
  merchant_id TEXT NOT NULL,
  bank_id UUID NOT NULL,

  name TEXT NULL,
  country TEXT NULL,

  schema_version TEXT NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_merchants_merchant_id_schema
  ON merchants (bank_id, merchant_id, schema_version);

-- Issuers (banks)
CREATE TABLE IF NOT EXISTS issuers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  issuer_id TEXT NOT NULL,
  bank_id UUID NOT NULL,
  name TEXT NULL,
  country TEXT NULL,

  schema_version TEXT NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_issuers_issuer_id_schema
  ON issuers (bank_id, issuer_id, schema_version);

-- Transactions (canonical facts)
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Business identifiers
  transaction_id TEXT NOT NULL,
  lifecycle_stage lifecycle_stage NOT NULL,
  bank_id UUID NOT NULL,

  amount NUMERIC(18, 6) NOT NULL,
  currency CHAR(3) NOT NULL,
  timestamp_utc TIMESTAMPTZ NOT NULL,

  card_network TEXT NOT NULL,

  merchant_pk UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
  issuer_pk UUID NULL REFERENCES issuers(id) ON DELETE RESTRICT,
  report_pk UUID NOT NULL REFERENCES reports(id) ON DELETE RESTRICT,

  -- Traceability
  raw_source_object_key TEXT NOT NULL,
  raw_source_artifact_id UUID NULL,

  -- Confidence
  confidence_score DOUBLE PRECISION NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),

  schema_version TEXT NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Deduplication enforced at DB level (idempotent upserts).
-- Canonical dedupe key aligns with Phase 3: (transaction_id, lifecycle_stage) per schema version.
CREATE UNIQUE INDEX IF NOT EXISTS uq_transactions_txid_stage_schema
  ON transactions (bank_id, transaction_id, lifecycle_stage, schema_version);

-- Required indexes
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_id
  ON transactions (bank_id, transaction_id);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant_pk
  ON transactions (bank_id, merchant_pk);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
  ON transactions (bank_id, timestamp_utc);

COMMIT;


