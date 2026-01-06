-- Phase 10.1 — Tenant isolation via PostgreSQL Row-Level Security (RLS)
-- Enforce bank_id isolation by design across canonical facts and explainability tables.
-- Connection must set: SET app.bank_id = '<uuid>';

BEGIN;

-- Helper function to read current tenant from session
CREATE OR REPLACE FUNCTION current_bank_id() RETURNS uuid AS $$
  SELECT current_setting('app.current_bank_id', true)::uuid;
$$ LANGUAGE sql STABLE;

-- Canonical facts tables
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;
ALTER TABLE issuers ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rls_reports ON reports;
CREATE POLICY rls_reports ON reports
  USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_merchants ON merchants;
CREATE POLICY rls_merchants ON merchants
  USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_issuers ON issuers;
CREATE POLICY rls_issuers ON issuers
  USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_transactions ON transactions;
CREATE POLICY rls_transactions ON transactions
  USING (bank_id = current_bank_id());

-- Timescale metrics tables (also Postgres tables)
ALTER TABLE transaction_volume ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE dispute_rates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rls_tv ON transaction_volume;
CREATE POLICY rls_tv ON transaction_volume USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_fc ON fraud_counts;
CREATE POLICY rls_fc ON fraud_counts USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_dr ON dispute_rates;
CREATE POLICY rls_dr ON dispute_rates USING (bank_id = current_bank_id());

-- Explainability tables: add bank_id + policies
ALTER TABLE prompt_versions ADD COLUMN IF NOT EXISTS bank_id uuid;
ALTER TABLE model_versions ADD COLUMN IF NOT EXISTS bank_id uuid;
ALTER TABLE schema_versions ADD COLUMN IF NOT EXISTS bank_id uuid;
ALTER TABLE ai_outputs ADD COLUMN IF NOT EXISTS bank_id uuid;
ALTER TABLE agent_decision_traces ADD COLUMN IF NOT EXISTS bank_id uuid;

ALTER TABLE prompt_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_decision_traces ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rls_prompt_versions ON prompt_versions;
CREATE POLICY rls_prompt_versions ON prompt_versions USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_model_versions ON model_versions;
CREATE POLICY rls_model_versions ON model_versions USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_schema_versions ON schema_versions;
CREATE POLICY rls_schema_versions ON schema_versions USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_ai_outputs ON ai_outputs;
CREATE POLICY rls_ai_outputs ON ai_outputs USING (bank_id = current_bank_id());

DROP POLICY IF EXISTS rls_agent_decision_traces ON agent_decision_traces;
CREATE POLICY rls_agent_decision_traces ON agent_decision_traces USING (bank_id = current_bank_id());

COMMIT;


