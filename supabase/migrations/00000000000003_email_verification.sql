-- Email verification + phone field + signup tokens.

ALTER TABLE vaktram.user_profiles
  ADD COLUMN IF NOT EXISTS phone varchar(32),
  ADD COLUMN IF NOT EXISTS email_verified_at timestamptz;

CREATE TABLE IF NOT EXISTS vaktram.email_verification_tokens (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
  token_hash  varchar(128) NOT NULL UNIQUE,
  purpose     varchar(32) NOT NULL DEFAULT 'verify_email',  -- verify_email | password_reset
  expires_at  timestamptz NOT NULL,
  used_at     timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_evt_user    ON vaktram.email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_evt_purpose ON vaktram.email_verification_tokens(purpose);

DROP TRIGGER IF EXISTS trg_touch_email_verification_tokens ON vaktram.email_verification_tokens;
CREATE TRIGGER trg_touch_email_verification_tokens
  BEFORE UPDATE ON vaktram.email_verification_tokens
  FOR EACH ROW EXECUTE FUNCTION vaktram.touch_updated_at();
