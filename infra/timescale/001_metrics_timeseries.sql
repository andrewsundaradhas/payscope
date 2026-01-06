-- Phase 4.2 — TimescaleDB metrics & time-series
-- Purpose: high-volume temporal metrics; append-only hypertables with retention + downsampling.

BEGIN;

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Base tables (append-only)
CREATE TABLE IF NOT EXISTS transaction_volume (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bucket_time TIMESTAMPTZ NOT NULL,
  bank_id UUID NOT NULL,
  source_network TEXT NOT NULL,
  lifecycle_stage TEXT NOT NULL,
  tx_count BIGINT NOT NULL CHECK (tx_count >= 0),
  amount_sum NUMERIC(24, 6) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fraud_counts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bucket_time TIMESTAMPTZ NOT NULL,
  bank_id UUID NOT NULL,
  source_network TEXT NOT NULL,
  lifecycle_stage TEXT NOT NULL,
  fraud_count BIGINT NOT NULL CHECK (fraud_count >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dispute_rates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bucket_time TIMESTAMPTZ NOT NULL,
  bank_id UUID NOT NULL,
  source_network TEXT NOT NULL,
  lifecycle_stage TEXT NOT NULL,
  dispute_count BIGINT NOT NULL CHECK (dispute_count >= 0),
  tx_count BIGINT NOT NULL CHECK (tx_count >= 0),
  dispute_rate DOUBLE PRECISION GENERATED ALWAYS AS (
    CASE WHEN tx_count = 0 THEN 0 ELSE (dispute_count::double precision / tx_count::double precision) END
  ) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Convert to hypertables (time-based partitioning)
SELECT create_hypertable('transaction_volume', 'bucket_time', if_not_exists => TRUE);
SELECT create_hypertable('fraud_counts', 'bucket_time', if_not_exists => TRUE);
SELECT create_hypertable('dispute_rates', 'bucket_time', if_not_exists => TRUE);

-- Append-only enforcement: prevent UPDATE/DELETE.
CREATE OR REPLACE FUNCTION _prevent_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'timeseries tables are append-only';
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'tr_no_update_transaction_volume') THEN
    CREATE TRIGGER tr_no_update_transaction_volume BEFORE UPDATE OR DELETE ON transaction_volume
      FOR EACH ROW EXECUTE FUNCTION _prevent_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'tr_no_update_fraud_counts') THEN
    CREATE TRIGGER tr_no_update_fraud_counts BEFORE UPDATE OR DELETE ON fraud_counts
      FOR EACH ROW EXECUTE FUNCTION _prevent_mutation();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'tr_no_update_dispute_rates') THEN
    CREATE TRIGGER tr_no_update_dispute_rates BEFORE UPDATE OR DELETE ON dispute_rates
      FOR EACH ROW EXECUTE FUNCTION _prevent_mutation();
  END IF;
END $$;

-- Indexes for aggregation queries
CREATE INDEX IF NOT EXISTS idx_tv_time_network_stage
  ON transaction_volume (bank_id, bucket_time DESC, source_network, lifecycle_stage);

CREATE INDEX IF NOT EXISTS idx_fc_time_network_stage
  ON fraud_counts (bank_id, bucket_time DESC, source_network, lifecycle_stage);

CREATE INDEX IF NOT EXISTS idx_dr_time_network_stage
  ON dispute_rates (bank_id, bucket_time DESC, source_network, lifecycle_stage);

-- Downsampling via continuous aggregates (hourly -> daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS transaction_volume_daily
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', bucket_time) AS day,
  bank_id,
  source_network,
  lifecycle_stage,
  SUM(tx_count) AS tx_count,
  SUM(amount_sum) AS amount_sum
FROM transaction_volume
GROUP BY 1,2,3,4;

SELECT add_continuous_aggregate_policy('transaction_volume_daily',
  start_offset => INTERVAL '30 days',
  end_offset   => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 hour'
);

-- Retention policies (compliance-friendly defaults)
-- Keep raw for 90 days, keep daily aggregate for 2 years.
SELECT add_retention_policy('transaction_volume', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('fraud_counts', INTERVAL '180 days', if_not_exists => TRUE);
SELECT add_retention_policy('dispute_rates', INTERVAL '365 days', if_not_exists => TRUE);

SELECT add_retention_policy('transaction_volume_daily', INTERVAL '2 years', if_not_exists => TRUE);

COMMIT;


