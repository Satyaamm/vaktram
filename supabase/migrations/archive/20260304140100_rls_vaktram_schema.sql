-- ============================================
-- Grant access to vaktram schema for Supabase roles
-- (RLS policies moved with the tables, just need grants)
-- ============================================

GRANT USAGE ON SCHEMA vaktram TO authenticated, anon, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA vaktram TO authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA vaktram TO anon;

-- Ensure future tables also get proper grants
ALTER DEFAULT PRIVILEGES IN SCHEMA vaktram
  GRANT ALL ON TABLES TO authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA vaktram
  GRANT SELECT ON TABLES TO anon;
