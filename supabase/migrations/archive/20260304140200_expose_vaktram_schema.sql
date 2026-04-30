-- Expose vaktram schema to PostgREST (Supabase Data API)
-- This allows supabase.schema("vaktram").from("table") to work
NOTIFY pgrst, 'reload schema';

-- Also ensure the authenticator role can access the schema
GRANT USAGE ON SCHEMA vaktram TO authenticator;
GRANT ALL ON ALL TABLES IN SCHEMA vaktram TO authenticator;
