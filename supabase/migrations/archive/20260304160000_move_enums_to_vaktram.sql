-- Move enum types back to vaktram schema (no public schema in prod)
ALTER TYPE public.meeting_status SET SCHEMA vaktram;
ALTER TYPE public.meeting_platform SET SCHEMA vaktram;
