-- Phase 5: compliance plumbing.

DO $$ BEGIN
  CREATE TYPE vaktram.data_export_kind AS ENUM ('gdpr','admin');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE vaktram.data_export_status AS ENUM ('pending','in_progress','ready','failed');
EXCEPTION WHEN duplicate_object THEN null; END $$;


CREATE TABLE IF NOT EXISTS vaktram.retention_policies (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id   uuid NOT NULL UNIQUE
                       REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
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
  organization_id   uuid NOT NULL UNIQUE
                       REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
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
