-- ============================================
-- Vaktram: Initial Schema (schema: vaktram)
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the vaktram schema
CREATE SCHEMA IF NOT EXISTS vaktram;

-- Set search path for this script
SET search_path TO vaktram;

-- Enums (must be created in the schema)
CREATE TYPE vaktram.meeting_status AS ENUM (
  'scheduled', 'in_progress', 'processing', 'transcribing',
  'summarizing', 'completed', 'cancelled', 'failed'
);

CREATE TYPE vaktram.meeting_platform AS ENUM (
  'google_meet', 'zoom', 'teams', 'other'
);

-- Organizations
CREATE TABLE vaktram.organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  logo_url TEXT,
  max_seats INTEGER NOT NULL DEFAULT 5,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- User Profiles
CREATE TABLE vaktram.user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  avatar_url TEXT,
  organization_id UUID REFERENCES vaktram.organizations(id),
  role VARCHAR(50) NOT NULL DEFAULT 'member',
  is_active BOOLEAN NOT NULL DEFAULT true,
  onboarding_completed BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Meetings
CREATE TABLE vaktram.meetings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES vaktram.user_profiles(id),
  organization_id UUID REFERENCES vaktram.organizations(id),
  title VARCHAR(500) NOT NULL,
  meeting_url TEXT,
  platform vaktram.meeting_platform NOT NULL DEFAULT 'google_meet',
  status vaktram.meeting_status NOT NULL DEFAULT 'scheduled',
  scheduled_start TIMESTAMPTZ,
  scheduled_end TIMESTAMPTZ,
  actual_start TIMESTAMPTZ,
  actual_end TIMESTAMPTZ,
  duration_seconds INTEGER,
  calendar_event_id VARCHAR(255),
  bot_id VARCHAR(255),
  metadata JSONB,
  auto_record BOOLEAN NOT NULL DEFAULT true,
  audio_url TEXT,
  transcript_ready BOOLEAN NOT NULL DEFAULT false,
  summary_ready BOOLEAN NOT NULL DEFAULT false,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_meetings_user_id ON vaktram.meetings(user_id);

-- Meeting Participants
CREATE TABLE vaktram.meeting_participants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meeting_id UUID NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  role VARCHAR(50),
  speaking_duration_seconds INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Transcript Segments
CREATE TABLE vaktram.transcript_segments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meeting_id UUID NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  speaker_name VARCHAR(255) NOT NULL,
  speaker_email VARCHAR(255),
  content TEXT NOT NULL,
  start_time DOUBLE PRECISION NOT NULL,
  end_time DOUBLE PRECISION NOT NULL,
  sequence_number INTEGER NOT NULL,
  confidence DOUBLE PRECISION,
  language VARCHAR(10) DEFAULT 'en',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_transcript_segments_meeting_id ON vaktram.transcript_segments(meeting_id);

-- Meeting Summaries
CREATE TABLE vaktram.meeting_summaries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meeting_id UUID NOT NULL UNIQUE REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  summary_text TEXT NOT NULL,
  action_items JSONB,
  key_decisions JSONB,
  topics JSONB,
  sentiment VARCHAR(50),
  model_used VARCHAR(100),
  provider_used VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_meeting_summaries_meeting_id ON vaktram.meeting_summaries(meeting_id);

-- User AI Configs (BYOM)
CREATE TABLE vaktram.user_ai_configs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,
  model_name VARCHAR(100) NOT NULL,
  api_key_encrypted TEXT,
  base_url TEXT,
  is_default BOOLEAN NOT NULL DEFAULT false,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_user_ai_configs_user_id ON vaktram.user_ai_configs(user_id);

-- Calendar Connections
CREATE TABLE vaktram.calendar_connections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,
  access_token_encrypted TEXT,
  refresh_token_encrypted TEXT,
  token_expires_at TIMESTAMPTZ,
  calendar_id VARCHAR(255),
  webhook_channel_id VARCHAR(255),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Meeting Embeddings
CREATE TABLE vaktram.meeting_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meeting_id UUID NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  segment_id UUID REFERENCES vaktram.transcript_segments(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding JSONB,
  embedding_model VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_meeting_embeddings_meeting_id ON vaktram.meeting_embeddings(meeting_id);

-- API Keys
CREATE TABLE vaktram.api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  key_hash VARCHAR(255) NOT NULL UNIQUE,
  key_prefix VARCHAR(10) NOT NULL,
  last_used_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Audit Logs
CREATE TABLE vaktram.audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES vaktram.user_profiles(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id VARCHAR(255),
  details JSONB,
  ip_address VARCHAR(45),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Notifications
CREATE TABLE vaktram.notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  body TEXT,
  notification_type VARCHAR(50) NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT false,
  link TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_user_id ON vaktram.notifications(user_id);

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION vaktram.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN
    SELECT unnest(ARRAY[
      'organizations', 'user_profiles', 'meetings', 'meeting_participants',
      'transcript_segments', 'meeting_summaries', 'user_ai_configs',
      'calendar_connections', 'meeting_embeddings', 'api_keys', 'notifications'
    ])
  LOOP
    EXECUTE format(
      'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON vaktram.%I FOR EACH ROW EXECUTE FUNCTION vaktram.update_updated_at()',
      t, t
    );
  END LOOP;
END;
$$;
