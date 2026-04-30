-- Phase 3: dead-letter queue.

DO $$ BEGIN
  CREATE TYPE vaktram.job_status AS ENUM
    ('pending','in_progress','succeeded','failed','dead_letter');
EXCEPTION WHEN duplicate_object THEN null; END $$;

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
CREATE INDEX IF NOT EXISTS ix_dlq_org ON vaktram.dead_letter_jobs(organization_id);
CREATE INDEX IF NOT EXISTS ix_dlq_kind ON vaktram.dead_letter_jobs(kind);
