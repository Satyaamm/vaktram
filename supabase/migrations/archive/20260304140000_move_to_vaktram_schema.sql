-- ============================================
-- Move all tables to "vaktram" schema
-- ============================================

CREATE SCHEMA IF NOT EXISTS vaktram;

-- Move tables
ALTER TABLE public.organizations SET SCHEMA vaktram;
ALTER TABLE public.user_profiles SET SCHEMA vaktram;
ALTER TABLE public.meetings SET SCHEMA vaktram;
ALTER TABLE public.meeting_participants SET SCHEMA vaktram;
ALTER TABLE public.transcript_segments SET SCHEMA vaktram;
ALTER TABLE public.meeting_summaries SET SCHEMA vaktram;
ALTER TABLE public.user_ai_configs SET SCHEMA vaktram;
ALTER TABLE public.calendar_connections SET SCHEMA vaktram;
ALTER TABLE public.meeting_embeddings SET SCHEMA vaktram;
ALTER TABLE public.api_keys SET SCHEMA vaktram;
ALTER TABLE public.audit_logs SET SCHEMA vaktram;
ALTER TABLE public.notifications SET SCHEMA vaktram;

-- Move the trigger function
ALTER FUNCTION public.update_updated_at() SET SCHEMA vaktram;

-- Move enum types
ALTER TYPE public.meeting_status SET SCHEMA vaktram;
ALTER TYPE public.meeting_platform SET SCHEMA vaktram;
