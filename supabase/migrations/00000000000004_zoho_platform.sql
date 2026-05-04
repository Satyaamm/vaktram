-- Add 'zoho' to the meeting_platform enum so calendar sync and the bot
-- service can persist Zoho Meeting events alongside google_meet/zoom/teams.
--
-- ALTER TYPE ... ADD VALUE is idempotent in Postgres only when guarded by
-- IF NOT EXISTS (Postgres 12+). Wrapped in DO/EXCEPTION so re-running this
-- migration on an already-patched DB is a no-op.

DO $$
BEGIN
    ALTER TYPE vaktram.meeting_platform ADD VALUE IF NOT EXISTS 'zoho';
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
