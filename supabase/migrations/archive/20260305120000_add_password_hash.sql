-- Add password_hash column for custom JWT auth
ALTER TABLE vaktram.user_profiles ADD COLUMN IF NOT EXISTS password_hash TEXT;
