-- Move enum types back to public schema so asyncpg can resolve them
-- asyncpg uses unqualified type names in prepared statements ($2::meeting_status)
-- and cannot find types in non-public schemas even with search_path set.

ALTER TYPE vaktram.meeting_status SET SCHEMA public;
ALTER TYPE vaktram.meeting_platform SET SCHEMA public;
