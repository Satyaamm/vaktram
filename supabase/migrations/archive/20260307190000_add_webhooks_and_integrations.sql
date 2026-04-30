-- Phase 9: outbound webhooks + Slack integration metadata.

DO $$ BEGIN
  CREATE TYPE vaktram.delivery_status AS ENUM ('pending','succeeded','failed','dead');
EXCEPTION WHEN duplicate_object THEN null; END $$;

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


-- Per-org integrations (Slack incoming webhook for now; one row per provider).
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
