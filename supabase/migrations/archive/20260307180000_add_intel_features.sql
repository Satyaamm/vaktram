-- Phase 8: Vaktram intel features — Channels, Topic Trackers, Soundbites, Ask (Vakta).

DO $$ BEGIN
  CREATE TYPE vaktram.ask_scope AS ENUM ('meeting','channel','organization');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- ── Channels ──────────────────────────────────────────────────────────
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
CREATE INDEX IF NOT EXISTS ix_channel_members_channel ON vaktram.channel_members(channel_id);

CREATE TABLE IF NOT EXISTS vaktram.channel_meetings (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id  uuid NOT NULL REFERENCES vaktram.channels(id) ON DELETE CASCADE,
  meeting_id  uuid NOT NULL REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_channel_meeting UNIQUE (channel_id, meeting_id)
);
CREATE INDEX IF NOT EXISTS ix_channel_meetings_channel ON vaktram.channel_meetings(channel_id);


-- ── Topic Tracker ─────────────────────────────────────────────────────
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
CREATE INDEX IF NOT EXISTS ix_topic_trackers_org ON vaktram.topic_trackers(organization_id);

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
CREATE INDEX IF NOT EXISTS ix_topic_hits_tracker ON vaktram.topic_hits(tracker_id);
CREATE INDEX IF NOT EXISTS ix_topic_hits_meeting ON vaktram.topic_hits(meeting_id);


-- ── Soundbites ────────────────────────────────────────────────────────
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
CREATE INDEX IF NOT EXISTS ix_soundbites_meeting ON vaktram.soundbites(meeting_id);


-- ── Ask (Vakta — chat with your meetings) ───────────────────────────
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
CREATE INDEX IF NOT EXISTS ix_ask_threads_user ON vaktram.ask_threads(user_id);

CREATE TABLE IF NOT EXISTS vaktram.ask_messages (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id   uuid NOT NULL REFERENCES vaktram.ask_threads(id) ON DELETE CASCADE,
  role        varchar(16) NOT NULL,
  content     text NOT NULL,
  citations   jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ask_messages_thread ON vaktram.ask_messages(thread_id);
