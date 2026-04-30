-- Scheduled jobs table for APScheduler persistence
CREATE TABLE IF NOT EXISTS vaktram.scheduled_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    meeting_id UUID REFERENCES vaktram.meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES vaktram.user_profiles(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    executed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result TEXT,
    error TEXT,
    payload JSONB,
    retries INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_type_status ON vaktram.scheduled_jobs(job_type, status);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_meeting_id ON vaktram.scheduled_jobs(meeting_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_user_id ON vaktram.scheduled_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_scheduled_at ON vaktram.scheduled_jobs(scheduled_at);

-- APScheduler job store table (used by APScheduler internally)
CREATE TABLE IF NOT EXISTS vaktram.apscheduler_jobs (
    id VARCHAR(191) PRIMARY KEY,
    next_run_time DOUBLE PRECISION,
    job_state BYTEA NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_apscheduler_next_run ON vaktram.apscheduler_jobs(next_run_time);
