-- Add timezone and language columns to user_profiles
ALTER TABLE vaktram.user_profiles ADD COLUMN IF NOT EXISTS timezone VARCHAR(100) DEFAULT 'UTC';
ALTER TABLE vaktram.user_profiles ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
