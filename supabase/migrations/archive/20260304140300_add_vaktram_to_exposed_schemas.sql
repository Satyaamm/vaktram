-- Add vaktram to the exposed schemas for PostgREST
-- This is needed for supabase.schema("vaktram").from("table") to work
ALTER ROLE authenticator SET pgrst.db_schemas TO 'public,vaktram';
NOTIFY pgrst, 'reload config';
