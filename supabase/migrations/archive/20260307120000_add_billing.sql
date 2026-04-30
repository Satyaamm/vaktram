-- Phase 1: Billing and usage metering.

-- ── Enums ─────────────────────────────────────────────────────────────
DO $$ BEGIN
  CREATE TYPE vaktram.plan_tier AS ENUM ('free','pro','team','business','enterprise');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE vaktram.subscription_status AS ENUM
    ('trialing','active','past_due','canceled','incomplete','paused');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE vaktram.usage_kind AS ENUM
    ('transcription_minutes','llm_input_tokens','llm_output_tokens',
     'bot_minutes','storage_gb_hours','seats');
EXCEPTION WHEN duplicate_object THEN null; END $$;


-- ── subscriptions ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vaktram.subscriptions (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id          uuid NOT NULL UNIQUE
                              REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS ix_subscriptions_customer
  ON vaktram.subscriptions(stripe_customer_id);


-- ── usage_events (append-only) ────────────────────────────────────────
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
CREATE INDEX IF NOT EXISTS ix_usage_events_org_kind_ts
  ON vaktram.usage_events(organization_id, kind, created_at DESC);


-- ── usage_period_summaries (rollup) ───────────────────────────────────
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


-- ── invoices ──────────────────────────────────────────────────────────
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
CREATE INDEX IF NOT EXISTS ix_invoices_org ON vaktram.invoices(organization_id);
