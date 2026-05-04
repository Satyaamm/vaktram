-- ================================================================
-- Vaktram — Consolidated initial schema
-- ================================================================
-- Replaces the original 20 incremental migrations. Idempotent: every
-- CREATE / ALTER guards with IF NOT EXISTS so this can be re-run safely.
-- ================================================================

-- ---- 1. Extensions ---------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- gen_random_uuid()
-- pgvector is intentionally NOT required here. Embeddings are stored as
-- JSONB and similarity is computed in-app (see search_service._vector).
-- When you outgrow that, enable pgvector in the Supabase dashboard and
-- run a small follow-up migration to add the embedding_v column + ivfflat
-- index — it's a pure performance optimization.

-- ---- 2. Schema + helper trigger function -----------------------------
CREATE SCHEMA IF NOT EXISTS vaktram;
SET search_path TO vaktram, public;

CREATE OR REPLACE FUNCTION vaktram.touch_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;

-- ---- 3. ENUMs --------------------------------------------------------
DO $$ BEGIN CREATE TYPE vaktram.meeting_status AS ENUM
  ('scheduled','in_progress','processing','transcribing',
   'summarizing','completed','cancelled','failed');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.meeting_platform AS ENUM
  ('google_meet','zoom','teams','zoho','other');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.plan_tier AS ENUM
  ('free','pro','team','business','enterprise');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.subscription_status AS ENUM
  ('trialing','active','past_due','canceled','incomplete','paused');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.usage_kind AS ENUM
  ('transcription_minutes','llm_input_tokens','llm_output_tokens',
   'bot_minutes','storage_gb_hours','seats');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.job_status AS ENUM
  ('pending','in_progress','succeeded','failed','dead_letter');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.sso_type AS ENUM ('saml','oidc');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.role_scope AS ENUM ('organization','team','meeting');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.data_export_kind AS ENUM ('gdpr','admin');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.data_export_status AS ENUM
  ('pending','in_progress','ready','failed');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.ask_scope AS ENUM ('meeting','channel','organization');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN CREATE TYPE vaktram.delivery_status AS ENUM
  ('pending','succeeded','failed','dead');
EXCEPTION WHEN duplicate_object THEN null; END $$;


-- ---- 4. Tenancy ------------------------------------------------------
CREATE TABLE IF NOT EXISTS vaktram.organizations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name            varchar(255) NOT NULL,
  slug            varchar(255) NOT NULL UNIQUE,
  logo_url        text,
  max_seats       integer NOT NULL DEFAULT 5,
  region          varchar(32) NOT NULL DEFAULT 'ap-southeast-1',
  storage_prefix  varchar(255),
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_orgs_region ON vaktram.organizations(region);

CREATE TABLE IF NOT EXISTS vaktram.user_profiles (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email                  varchar(255) NOT NULL UNIQUE,
  full_name              varchar(255),
  avatar_url             text,
  organization_id        uuid REFERENCES vaktram.organizations(id) ON DELETE SET NULL,
  role                   varchar(50) NOT NULL DEFAULT 'member',
  is_active              boolean NOT NULL DEFAULT true,
  onboarding_completed   boolean NOT NULL DEFAULT false,
  timezone               varchar(100) DEFAULT 'UTC',
  language               varchar(10) DEFAULT 'en',
  password_hash          text,
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_org ON vaktram.user_profiles(organization_id);

CREATE TABLE IF NOT EXISTS vaktram.calendar_connections (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                  uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  provider                 varchar(50) NOT NULL,
  access_token_encrypted   text,
  refresh_token_encrypted  text,
  token_expires_at         timestamptz,
  calendar_id              varchar(255),
  webhook_channel_id       varchar(255),
  is_active                boolean NOT NULL DEFAULT true,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cal_user ON vaktram.calendar_connections(user_id);

CREATE TABLE IF NOT EXISTS vaktram.api_keys (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  name          varchar(100) NOT NULL,
  key_hash      varchar(255) NOT NULL UNIQUE,
  key_prefix    varchar(10)  NOT NULL,
  last_used_at  timestamptz,
  expires_at    timestamptz,
  is_active     boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);


-- ---- 5. Meeting domain ----------------------------------------------
CREATE TABLE IF NOT EXISTS vaktram.meetings (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid NOT NULL REFERENCES vaktram.user_profiles(id),
  organization_id     uuid REFERENCES vaktram.organizations(id),
  title               varchar(500) NOT NULL,
  meeting_url         text,
  platform            vaktram.meeting_platform NOT NULL DEFAULT 'google_meet',
  status              vaktram.meeting_status   NOT NULL DEFAULT 'scheduled',
  scheduled_start     timestamptz,
  scheduled_end       timestamptz,
  actual_start        timestamptz,
  actual_end          timestamptz,
  duration_seconds    integer,
  calendar_event_id   varchar(255),
  bot_id              varchar(255),
  metadata            jsonb,
  auto_record         boolean NOT NULL DEFAULT true,
  audio_url           text,
  transcript_ready    boolean NOT NULL DEFAULT false,
  summary_ready       boolean NOT NULL DEFAULT false,
  error_message       text,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_meetings_user ON vaktram.meetings(user_id);
CREATE INDEX IF NOT EXISTS ix_meetings_org  ON vaktram.meetings(organization_id);
CREATE INDEX IF NOT EXISTS ix_meetings_status_start
  ON vaktram.meetings(status, scheduled_start);

CREATE TABLE IF NOT EXISTS vaktram.meeting_participants (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id                  uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  name                        varchar(255) NOT NULL,
  email                       varchar(255),
  role                        varchar(50),
  speaking_duration_seconds   integer,
  created_at                  timestamptz NOT NULL DEFAULT now(),
  updated_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vaktram.transcript_segments (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id          uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  speaker_name        varchar(255) NOT NULL,
  speaker_email       varchar(255),
  content             text NOT NULL,
  start_time          double precision NOT NULL,
  end_time            double precision NOT NULL,
  sequence_number     integer NOT NULL,
  confidence          double precision,
  language            varchar(10) DEFAULT 'en',
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_segments_meeting ON vaktram.transcript_segments(meeting_id);
CREATE INDEX IF NOT EXISTS ix_segments_fts
  ON vaktram.transcript_segments
  USING GIN (to_tsvector('english', content));

CREATE TABLE IF NOT EXISTS vaktram.meeting_summaries (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id      uuid NOT NULL UNIQUE REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  summary_text    text NOT NULL,
  action_items    jsonb,
  key_decisions   jsonb,
  topics          jsonb,
  sentiment       varchar(50),
  model_used      varchar(100),
  provider_used   varchar(100),
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vaktram.meeting_embeddings (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id        uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  segment_id        uuid REFERENCES vaktram.transcript_segments(id) ON DELETE CASCADE,
  content           text NOT NULL,
  embedding         jsonb,                          -- BYOM-flexible
  embedding_model   varchar(100),
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_embeddings_meeting ON vaktram.meeting_embeddings(meeting_id);
CREATE INDEX IF NOT EXISTS ix_embeddings_model   ON vaktram.meeting_embeddings(embedding_model);


-- ---- 6. Identity, RBAC, AI configs ----------------------------------
CREATE TABLE IF NOT EXISTS vaktram.user_ai_configs (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id              uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  provider             varchar(50) NOT NULL,
  model_name           varchar(100) NOT NULL,
  api_key_encrypted    text,
  base_url             text,
  extra_config         jsonb DEFAULT '{}',
  is_default           boolean NOT NULL DEFAULT false,
  is_active            boolean NOT NULL DEFAULT true,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_aiconfig_user ON vaktram.user_ai_configs(user_id);

CREATE TABLE IF NOT EXISTS vaktram.sso_connections (
  id                            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id               uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  type                          vaktram.sso_type NOT NULL,
  domain                        varchar(255) NOT NULL,
  is_active                     boolean NOT NULL DEFAULT true,
  idp_metadata_xml              text,
  idp_entity_id                 varchar(500),
  idp_sso_url                   varchar(500),
  idp_x509_cert                 text,
  oidc_issuer                   varchar(500),
  oidc_client_id                varchar(255),
  oidc_client_secret_encrypted  text,
  attribute_map                 jsonb,
  group_role_map                jsonb,
  created_at                    timestamptz NOT NULL DEFAULT now(),
  updated_at                    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sso_org    ON vaktram.sso_connections(organization_id);
CREATE INDEX IF NOT EXISTS ix_sso_domain ON vaktram.sso_connections(domain);

CREATE TABLE IF NOT EXISTS vaktram.scim_tokens (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  name              varchar(100) NOT NULL,
  token_hash        varchar(128) NOT NULL UNIQUE,
  token_prefix      varchar(12)  NOT NULL,
  last_used_at      timestamptz,
  expires_at        timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vaktram.roles (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  name              varchar(64) NOT NULL,
  description       varchar(255),
  permissions       text[] NOT NULL DEFAULT '{}',
  is_system         boolean NOT NULL DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_role_org_name UNIQUE (organization_id, name)
);

CREATE TABLE IF NOT EXISTS vaktram.role_assignments (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  role_id      uuid NOT NULL REFERENCES vaktram.roles(id) ON DELETE CASCADE,
  scope        vaktram.role_scope NOT NULL,
  scope_id     uuid,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ra_user ON vaktram.role_assignments(user_id);


-- ---- 7. Billing -----------------------------------------------------
CREATE TABLE IF NOT EXISTS vaktram.subscriptions (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id          uuid NOT NULL UNIQUE REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  stripe_customer_id       varchar(255),
  stripe_subscription_id   varchar(255) UNIQUE,
  plan                     vaktram.plan_tier NOT NULL DEFAULT 'free',
  status                   vaktram.subscription_status NOT NULL DEFAULT 'trialing',
  seats                    integer NOT NULL DEFAULT 1,
  trial_ends_at            timestamptz,
  current_period_start     timestamptz,
  current_period_end       timestamptz,
  cancel_at_period_end     boolean NOT NULL DEFAULT false,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_subs_customer ON vaktram.subscriptions(stripe_customer_id);

CREATE TABLE IF NOT EXISTS vaktram.usage_events (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  user_id           uuid REFERENCES vaktram.user_profiles(id) ON DELETE SET NULL,
  meeting_id        uuid REFERENCES vaktram.meetings(id) ON DELETE SET NULL,
  kind              vaktram.usage_kind NOT NULL,
  quantity          bigint NOT NULL,
  metadata          jsonb,
  created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_usage_org_kind_ts
  ON vaktram.usage_events(organization_id, kind, created_at DESC);

CREATE TABLE IF NOT EXISTS vaktram.usage_period_summaries (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  kind              vaktram.usage_kind NOT NULL,
  period_start      timestamptz NOT NULL,
  period_end        timestamptz NOT NULL,
  total             bigint NOT NULL DEFAULT 0,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_usage_period UNIQUE (organization_id, kind, period_start)
);

CREATE TABLE IF NOT EXISTS vaktram.invoices (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id     uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  stripe_invoice_id   varchar(255) NOT NULL UNIQUE,
  amount_cents        bigint NOT NULL,
  currency            varchar(8) NOT NULL DEFAULT 'usd',
  status              varchar(32) NOT NULL,
  hosted_url          varchar(500),
  pdf_url             varchar(500),
  issued_at           timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);


-- ---- 8. Compliance --------------------------------------------------
CREATE TABLE IF NOT EXISTS vaktram.audit_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES vaktram.user_profiles(id) ON DELETE SET NULL,
  action          varchar(100) NOT NULL,
  resource_type   varchar(50) NOT NULL,
  resource_id     varchar(255),
  details         jsonb,
  ip_address      varchar(45),
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_audit_created ON vaktram.audit_logs(created_at DESC);

CREATE TABLE IF NOT EXISTS vaktram.retention_policies (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL UNIQUE REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  default_days      integer NOT NULL DEFAULT 365,
  audio_days        integer,
  transcript_days   integer,
  summary_days      integer,
  legal_hold        boolean NOT NULL DEFAULT false,
  overrides         jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vaktram.kms_keys (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL UNIQUE REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  provider          varchar(32) NOT NULL,
  key_arn           varchar(500) NOT NULL,
  enabled           boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vaktram.data_export_requests (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  user_id           uuid REFERENCES vaktram.user_profiles(id) ON DELETE SET NULL,
  kind              vaktram.data_export_kind NOT NULL,
  status            vaktram.data_export_status NOT NULL DEFAULT 'pending',
  signed_url        text,
  expires_at        timestamptz,
  error             text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_export_org ON vaktram.data_export_requests(organization_id);


-- ---- 9. Operations: jobs, DLQ, webhooks, integrations ---------------
CREATE TABLE IF NOT EXISTS vaktram.scheduled_jobs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type      varchar(50) NOT NULL,
  meeting_id    uuid REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  user_id       uuid REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  scheduled_at  timestamptz NOT NULL,
  executed_at   timestamptz,
  status        varchar(20) NOT NULL DEFAULT 'pending',
  result        text,
  error         text,
  payload       jsonb,
  retries       integer NOT NULL DEFAULT 0,
  max_retries   integer NOT NULL DEFAULT 3,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sj_kind     ON vaktram.scheduled_jobs(job_type);
CREATE INDEX IF NOT EXISTS ix_sj_meeting  ON vaktram.scheduled_jobs(meeting_id);
CREATE INDEX IF NOT EXISTS ix_sj_user     ON vaktram.scheduled_jobs(user_id);
CREATE INDEX IF NOT EXISTS ix_sj_when     ON vaktram.scheduled_jobs(scheduled_at);

CREATE TABLE IF NOT EXISTS vaktram.dead_letter_jobs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid REFERENCES vaktram.organizations(id) ON DELETE SET NULL,
  meeting_id        uuid REFERENCES vaktram.meetings(id) ON DELETE SET NULL,
  kind              varchar(64) NOT NULL,
  payload           jsonb NOT NULL,
  error             text,
  attempts          integer NOT NULL DEFAULT 0,
  status            vaktram.job_status NOT NULL DEFAULT 'dead_letter',
  last_attempt_at   timestamptz,
  next_retry_at     timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_dlq_org   ON vaktram.dead_letter_jobs(organization_id);
CREATE INDEX IF NOT EXISTS ix_dlq_kind  ON vaktram.dead_letter_jobs(kind);

CREATE TABLE IF NOT EXISTS vaktram.webhook_endpoints (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  url             varchar(500) NOT NULL,
  description     varchar(255),
  secret          varchar(128) NOT NULL,
  events          text[] NOT NULL DEFAULT '{}',
  is_active       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_whe_org ON vaktram.webhook_endpoints(organization_id);

CREATE TABLE IF NOT EXISTS vaktram.webhook_deliveries (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint_id       uuid NOT NULL REFERENCES vaktram.webhook_endpoints(id) ON DELETE CASCADE,
  event             varchar(64) NOT NULL,
  payload           jsonb NOT NULL,
  status            vaktram.delivery_status NOT NULL DEFAULT 'pending',
  attempts          integer NOT NULL DEFAULT 0,
  last_status_code  integer,
  last_error        text,
  next_retry_at     timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_whd_endpoint ON vaktram.webhook_deliveries(endpoint_id);
CREATE INDEX IF NOT EXISTS ix_whd_retry
  ON vaktram.webhook_deliveries(next_retry_at)
  WHERE status = 'failed';

CREATE TABLE IF NOT EXISTS vaktram.org_integrations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  provider        varchar(32) NOT NULL,
  config          jsonb NOT NULL DEFAULT '{}',
  is_active       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_org_provider UNIQUE (organization_id, provider)
);


-- ---- 10. Notifications ----------------------------------------------
CREATE TABLE IF NOT EXISTS vaktram.notifications (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  title               varchar(255) NOT NULL,
  body                text,
  notification_type   varchar(50) NOT NULL,
  is_read             boolean NOT NULL DEFAULT false,
  link                text,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_notif_user ON vaktram.notifications(user_id);


-- ---- 11. Intel features (Channels / Topic / Soundbite / Ask) --------
CREATE TABLE IF NOT EXISTS vaktram.channels (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  name            varchar(120) NOT NULL,
  slug            varchar(120) NOT NULL,
  description     text,
  is_private      boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_channel_org_slug UNIQUE (organization_id, slug)
);
CREATE INDEX IF NOT EXISTS ix_channels_org ON vaktram.channels(organization_id);

CREATE TABLE IF NOT EXISTS vaktram.channel_members (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id  uuid NOT NULL REFERENCES vaktram.channels(id) ON DELETE CASCADE,
  user_id     uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  role        varchar(32) NOT NULL DEFAULT 'member',
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_cm_channel ON vaktram.channel_members(channel_id);

CREATE TABLE IF NOT EXISTS vaktram.channel_meetings (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id  uuid NOT NULL REFERENCES vaktram.channels(id) ON DELETE CASCADE,
  meeting_id  uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_channel_meeting UNIQUE (channel_id, meeting_id)
);
CREATE INDEX IF NOT EXISTS ix_chm_channel ON vaktram.channel_meetings(channel_id);

CREATE TABLE IF NOT EXISTS vaktram.topic_trackers (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
  name            varchar(120) NOT NULL,
  keywords        text[] NOT NULL DEFAULT '{}',
  is_active       boolean NOT NULL DEFAULT true,
  notify_emails   text[] NOT NULL DEFAULT '{}',
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_tt_org ON vaktram.topic_trackers(organization_id);

CREATE TABLE IF NOT EXISTS vaktram.topic_hits (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tracker_id          uuid NOT NULL REFERENCES vaktram.topic_trackers(id) ON DELETE CASCADE,
  meeting_id          uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  segment_id          uuid REFERENCES vaktram.transcript_segments(id) ON DELETE CASCADE,
  matched_keyword     varchar(120) NOT NULL,
  snippet             text NOT NULL,
  timestamp_seconds   double precision,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_th_tracker ON vaktram.topic_hits(tracker_id);
CREATE INDEX IF NOT EXISTS ix_th_meeting ON vaktram.topic_hits(meeting_id);

CREATE TABLE IF NOT EXISTS vaktram.soundbites (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id      uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  user_id         uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  title           varchar(255),
  start_seconds   double precision NOT NULL,
  end_seconds     double precision NOT NULL,
  transcript      text,
  share_token     varchar(64) UNIQUE,
  audio_url       text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sb_meeting ON vaktram.soundbites(meeting_id);

CREATE TABLE IF NOT EXISTS vaktram.ask_threads (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  organization_id uuid REFERENCES vaktram.organizations(id) ON DELETE SET NULL,
  title           varchar(255),
  scope           vaktram.ask_scope NOT NULL DEFAULT 'organization',
  scope_id        uuid,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_at_user ON vaktram.ask_threads(user_id);

CREATE TABLE IF NOT EXISTS vaktram.ask_messages (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id   uuid NOT NULL REFERENCES vaktram.ask_threads(id) ON DELETE CASCADE,
  role        varchar(16) NOT NULL,
  content     text NOT NULL,
  citations   jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_am_thread ON vaktram.ask_messages(thread_id);


-- ---- 12. updated_at triggers ----------------------------------------
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT t.table_name
    FROM information_schema.tables t
    JOIN information_schema.columns c
      ON c.table_schema = t.table_schema AND c.table_name = t.table_name
    WHERE t.table_schema = 'vaktram'
      AND t.table_type = 'BASE TABLE'
      AND c.column_name = 'updated_at'
  LOOP
    EXECUTE format(
      'DROP TRIGGER IF EXISTS trg_touch_%1$s ON vaktram.%1$I;'
      'CREATE TRIGGER trg_touch_%1$s BEFORE UPDATE ON vaktram.%1$I '
      'FOR EACH ROW EXECUTE FUNCTION vaktram.touch_updated_at();',
      r.table_name);
  END LOOP;
END $$;


-- ---- 13. Seed system roles ------------------------------------------
INSERT INTO vaktram.roles (name, description, permissions, is_system) VALUES
  ('owner',  'Full control of the workspace',
    ARRAY['meeting:read','meeting:write','meeting:delete','meeting:share',
          'transcript:export','billing:manage','team:manage','sso:manage',
          'audit:read','integration:manage'], true),
  ('admin',  'Workspace admin (no billing)',
    ARRAY['meeting:read','meeting:write','meeting:delete','meeting:share',
          'transcript:export','team:manage','sso:manage',
          'audit:read','integration:manage'], true),
  ('member', 'Standard member',
    ARRAY['meeting:read','meeting:write','meeting:share','transcript:export'], true),
  ('viewer', 'Read-only',
    ARRAY['meeting:read'], true),
  ('auditor','Read-only with audit access',
    ARRAY['meeting:read','audit:read'], true)
ON CONFLICT (organization_id, name) DO NOTHING;


-- ---- 14. Expose schema to PostgREST (Supabase data API) -------------
DO $$ BEGIN
  GRANT USAGE ON SCHEMA vaktram TO anon, authenticated, service_role;
  GRANT ALL ON ALL TABLES IN SCHEMA vaktram TO anon, authenticated, service_role;
  GRANT ALL ON ALL SEQUENCES IN SCHEMA vaktram TO anon, authenticated, service_role;
  ALTER DEFAULT PRIVILEGES IN SCHEMA vaktram GRANT ALL ON TABLES TO anon, authenticated, service_role;
  ALTER DEFAULT PRIVILEGES IN SCHEMA vaktram GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
EXCEPTION WHEN undefined_object THEN
  RAISE NOTICE 'Some Supabase roles missing; skipping grants';
END $$;
