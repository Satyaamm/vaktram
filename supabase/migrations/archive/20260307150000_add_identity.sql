-- Phase 4: Enterprise identity — SSO connections, SCIM tokens, RBAC.

DO $$ BEGIN
  CREATE TYPE vaktram.sso_type AS ENUM ('saml','oidc');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE vaktram.role_scope AS ENUM ('organization','team','meeting');
EXCEPTION WHEN duplicate_object THEN null; END $$;


CREATE TABLE IF NOT EXISTS vaktram.sso_connections (
  id                            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id               uuid NOT NULL
                                  REFERENCES vaktram.organizations(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS ix_scim_org ON vaktram.scim_tokens(organization_id);


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
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  role_id     uuid NOT NULL REFERENCES vaktram.roles(id) ON DELETE CASCADE,
  scope       vaktram.role_scope NOT NULL,
  scope_id    uuid,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_role_assignments_user ON vaktram.role_assignments(user_id);


-- Seed system roles (org_id NULL means platform-global templates).
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
ON CONFLICT DO NOTHING;
