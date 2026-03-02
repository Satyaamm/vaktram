-- ==========================================================================
-- Vaktram Database Schema (Supabase / PostgreSQL)
-- ==========================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings

-- ==========================================================================
-- ORGANIZATIONS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    plan            TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    owner_id        UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    logo_url        TEXT,
    settings        JSONB DEFAULT '{}',
    meetings_this_month INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_owner ON organizations(owner_id);

-- ==========================================================================
-- ORGANIZATION MEMBERS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS organization_members (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role            TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    invited_by      UUID REFERENCES auth.users(id),
    joined_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_org_members_org ON organization_members(organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);

-- ==========================================================================
-- MEETINGS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS meetings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title           TEXT NOT NULL DEFAULT 'Untitled Meeting',
    platform        TEXT NOT NULL CHECK (platform IN ('google_meet', 'zoom', 'teams')),
    meeting_url     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'scheduled'
                    CHECK (status IN ('scheduled', 'joining', 'in_progress', 'processing', 'completed', 'failed', 'cancelled')),
    scheduled_at    TIMESTAMPTZ,
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    duration_seconds INTEGER,
    participant_count INTEGER DEFAULT 0,
    bot_name        TEXT DEFAULT 'Vaktram Notetaker',
    audio_storage_path TEXT,
    created_by      UUID REFERENCES auth.users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meetings_org ON meetings(organization_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_created_by ON meetings(created_by);
CREATE INDEX idx_meetings_scheduled ON meetings(scheduled_at);
CREATE INDEX idx_meetings_org_status ON meetings(organization_id, status);

-- ==========================================================================
-- MEETING PARTICIPANTS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS meeting_participants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES auth.users(id),
    display_name    TEXT NOT NULL,
    email           TEXT,
    speaker_label   TEXT,  -- maps to diarization speaker label (SPEAKER_00, etc.)
    joined_at       TIMESTAMPTZ,
    left_at         TIMESTAMPTZ
);

CREATE INDEX idx_participants_meeting ON meeting_participants(meeting_id);
CREATE INDEX idx_participants_user ON meeting_participants(user_id);

-- ==========================================================================
-- TRANSCRIPTION JOBS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS transcription_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    audio_storage_path TEXT,
    segment_count   INTEGER DEFAULT 0,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_transcription_jobs_meeting ON transcription_jobs(meeting_id);
CREATE INDEX idx_transcription_jobs_status ON transcription_jobs(status);

-- ==========================================================================
-- TRANSCRIPT SEGMENTS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS transcript_segments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    speaker_label   TEXT NOT NULL,
    start_time      FLOAT NOT NULL,
    end_time        FLOAT NOT NULL,
    text            TEXT NOT NULL,
    confidence      FLOAT DEFAULT 0.0,
    language        TEXT DEFAULT 'en',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_segments_meeting ON transcript_segments(meeting_id);
CREATE INDEX idx_segments_meeting_time ON transcript_segments(meeting_id, start_time);
CREATE INDEX idx_segments_speaker ON transcript_segments(meeting_id, speaker_label);

-- ==========================================================================
-- SUMMARIZATION JOBS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS summarization_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_summarization_jobs_meeting ON summarization_jobs(meeting_id);
CREATE INDEX idx_summarization_jobs_status ON summarization_jobs(status);

-- ==========================================================================
-- MEETING SUMMARIES
-- ==========================================================================

CREATE TABLE IF NOT EXISTS meeting_summaries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id      UUID UNIQUE NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    summary         TEXT,
    action_items    JSONB DEFAULT '[]',
    decisions       JSONB DEFAULT '[]',
    follow_ups      JSONB DEFAULT '[]',
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    model_used      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_summaries_meeting ON meeting_summaries(meeting_id);

-- ==========================================================================
-- TRANSCRIPT EMBEDDINGS (pgvector)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS transcript_embeddings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       vector(384),  -- all-MiniLM-L6-v2 dimension
    is_summary      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_embeddings_meeting ON transcript_embeddings(meeting_id);

-- Create an IVFFlat index for similarity search (run after inserting some data)
-- CREATE INDEX idx_embeddings_vector ON transcript_embeddings
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ==========================================================================
-- BYOM (Bring Your Own Model) CONFIGURATIONS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS byom_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL CHECK (provider IN ('openai', 'anthropic', 'google', 'azure', 'groq', 'together', 'ollama')),
    model_name      TEXT NOT NULL,
    api_key_encrypted TEXT,  -- encrypted API key
    base_url        TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, provider, model_name)
);

CREATE INDEX idx_byom_org ON byom_configs(organization_id);

-- ==========================================================================
-- CALENDAR INTEGRATIONS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS calendar_integrations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL CHECK (provider IN ('google', 'outlook', 'apple')),
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    calendar_id     TEXT,
    auto_join       BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

CREATE INDEX idx_calendar_user ON calendar_integrations(user_id);

-- ==========================================================================
-- WEBHOOKS
-- ==========================================================================

CREATE TABLE IF NOT EXISTS webhooks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    events          TEXT[] DEFAULT ARRAY['meeting.completed'],
    secret          TEXT NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_webhooks_org ON webhooks(organization_id);

-- ==========================================================================
-- AUDIT LOG
-- ==========================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES auth.users(id),
    action          TEXT NOT NULL,
    resource_type   TEXT,
    resource_id     UUID,
    metadata        JSONB DEFAULT '{}',
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_org ON audit_log(organization_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- ==========================================================================
-- ROW LEVEL SECURITY (RLS)
-- ==========================================================================

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcript_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcript_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE byom_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Organizations: members can view, owners/admins can update
CREATE POLICY "org_select" ON organizations FOR SELECT
    USING (id IN (SELECT organization_id FROM organization_members WHERE user_id = auth.uid()));

CREATE POLICY "org_update" ON organizations FOR UPDATE
    USING (id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
    ));

-- Organization Members: members of the same org can view
CREATE POLICY "org_members_select" ON organization_members FOR SELECT
    USING (organization_id IN (
        SELECT organization_id FROM organization_members WHERE user_id = auth.uid()
    ));

-- Meetings: org members can view their org's meetings
CREATE POLICY "meetings_select" ON meetings FOR SELECT
    USING (organization_id IN (
        SELECT organization_id FROM organization_members WHERE user_id = auth.uid()
    ));

CREATE POLICY "meetings_insert" ON meetings FOR INSERT
    WITH CHECK (organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND role IN ('owner', 'admin', 'member')
    ));

-- Transcript Segments: same org members can read
CREATE POLICY "segments_select" ON transcript_segments FOR SELECT
    USING (meeting_id IN (
        SELECT m.id FROM meetings m
        JOIN organization_members om ON m.organization_id = om.organization_id
        WHERE om.user_id = auth.uid()
    ));

-- Meeting Summaries: same org members can read
CREATE POLICY "summaries_select" ON meeting_summaries FOR SELECT
    USING (meeting_id IN (
        SELECT m.id FROM meetings m
        JOIN organization_members om ON m.organization_id = om.organization_id
        WHERE om.user_id = auth.uid()
    ));

-- Calendar Integrations: users can only access their own
CREATE POLICY "calendar_select" ON calendar_integrations FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "calendar_all" ON calendar_integrations FOR ALL
    USING (user_id = auth.uid());

-- BYOM Configs: org owners/admins only
CREATE POLICY "byom_select" ON byom_configs FOR SELECT
    USING (organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
    ));

CREATE POLICY "byom_all" ON byom_configs FOR ALL
    USING (organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
    ));

-- Audit Log: org owners/admins can view
CREATE POLICY "audit_select" ON audit_log FOR SELECT
    USING (organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
    ));

-- ==========================================================================
-- TRIGGERS
-- ==========================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_organizations_updated
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_meetings_updated
    BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_summaries_updated
    BEFORE UPDATE ON meeting_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_byom_updated
    BEFORE UPDATE ON byom_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_calendar_updated
    BEFORE UPDATE ON calendar_integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_webhooks_updated
    BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-calculate meeting duration when ended_at is set
CREATE OR REPLACE FUNCTION calculate_meeting_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.ended_at - NEW.started_at))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_meeting_duration
    BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION calculate_meeting_duration();

-- Increment monthly meeting counter
CREATE OR REPLACE FUNCTION increment_meeting_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE organizations
    SET meetings_this_month = meetings_this_month + 1
    WHERE id = NEW.organization_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_increment_meeting_count
    AFTER INSERT ON meetings
    FOR EACH ROW EXECUTE FUNCTION increment_meeting_count();

-- ==========================================================================
-- FUNCTIONS
-- ==========================================================================

-- Semantic search function using pgvector
CREATE OR REPLACE FUNCTION search_transcripts(
    query_embedding vector(384),
    match_count INTEGER DEFAULT 10,
    org_id UUID DEFAULT NULL
)
RETURNS TABLE (
    meeting_id UUID,
    chunk_text TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        te.meeting_id,
        te.chunk_text,
        1 - (te.embedding <=> query_embedding) AS similarity
    FROM transcript_embeddings te
    JOIN meetings m ON te.meeting_id = m.id
    WHERE (org_id IS NULL OR m.organization_id = org_id)
    ORDER BY te.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Reset monthly meeting counts (run via cron)
CREATE OR REPLACE FUNCTION reset_monthly_meeting_counts()
RETURNS VOID AS $$
BEGIN
    UPDATE organizations SET meetings_this_month = 0;
END;
$$ LANGUAGE plpgsql;
