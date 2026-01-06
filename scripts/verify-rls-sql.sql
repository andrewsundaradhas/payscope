-- Verification queries for RLS and bank_id
-- Run these after migrations are complete

-- 1. Check table structure and bank_id columns
\d+ reports;
\d+ transactions;

-- 2. Check if bank_id columns exist
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('reports', 'transactions', 'transaction_volume')
  AND column_name = 'bank_id'
ORDER BY table_name;

-- 3. Check RLS is enabled
SELECT 
    relname AS table_name,
    relrowsecurity AS rls_enabled
FROM pg_class
WHERE relname IN ('reports', 'transactions', 'transaction_volume')
ORDER BY relname;

-- 4. List all RLS policies
SELECT 
    polname AS policy_name,
    tablename AS table_name,
    polcmd AS command,
    polqual AS using_expression,
    polwithcheck AS with_check_expression
FROM pg_policies
WHERE tablename IN ('reports', 'transactions', 'transaction_volume')
ORDER BY tablename, polname;

-- 5. Check TimescaleDB hypertables
SELECT 
    hypertable_name,
    num_dimensions,
    compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'transaction_volume';

-- 6. Verify bank_id in transaction_volume
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'transaction_volume'
  AND column_name = 'bank_id';

-- Expected results:
-- - All tables should have bank_id column (UUID type)
-- - RLS should be enabled (relrowsecurity = true)
-- - At least one policy per table (enforcing bank_id isolation)
-- - transaction_volume should be a hypertable with bank_id



