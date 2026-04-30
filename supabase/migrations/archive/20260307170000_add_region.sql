-- Phase 6: per-org region pin and storage prefix.
-- An org pinned to "eu-west-1" should never have its data egress to a US bucket.

ALTER TABLE vaktram.organizations
  ADD COLUMN IF NOT EXISTS region varchar(32) NOT NULL DEFAULT 'us-east-1',
  ADD COLUMN IF NOT EXISTS storage_prefix varchar(255);

CREATE INDEX IF NOT EXISTS ix_orgs_region ON vaktram.organizations(region);
