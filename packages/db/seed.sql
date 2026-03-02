-- ==========================================================================
-- Seed Data for Development
-- ==========================================================================
-- NOTE: This assumes a test user exists in auth.users.
-- In development, create a user via Supabase Auth first, then replace
-- the UUID below with the actual user ID.

-- Placeholder user ID (replace with real Supabase Auth user ID)
DO $$
DECLARE
    test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    org_id UUID;
    meeting_id_1 UUID;
    meeting_id_2 UUID;
BEGIN

-- ---------------------------------------------------------------------------
-- Seed Organization
-- ---------------------------------------------------------------------------

INSERT INTO organizations (id, name, slug, plan, owner_id)
VALUES (
    uuid_generate_v4(),
    'Acme Corp',
    'acme-corp',
    'pro',
    test_user_id
) RETURNING id INTO org_id;

-- Add owner as org member
INSERT INTO organization_members (organization_id, user_id, role)
VALUES (org_id, test_user_id, 'owner');

-- ---------------------------------------------------------------------------
-- Seed Meetings
-- ---------------------------------------------------------------------------

INSERT INTO meetings (id, organization_id, title, platform, meeting_url, status, created_by, started_at, ended_at, participant_count)
VALUES (
    uuid_generate_v4(),
    org_id,
    'Weekly Standup - Sprint 12',
    'google_meet',
    'https://meet.google.com/abc-defg-hij',
    'completed',
    test_user_id,
    NOW() - INTERVAL '2 hours',
    NOW() - INTERVAL '1 hour 30 minutes',
    4
) RETURNING id INTO meeting_id_1;

INSERT INTO meetings (id, organization_id, title, platform, meeting_url, status, created_by, scheduled_at)
VALUES (
    uuid_generate_v4(),
    org_id,
    'Product Roadmap Review',
    'google_meet',
    'https://meet.google.com/xyz-abcd-efg',
    'scheduled',
    test_user_id,
    NOW() + INTERVAL '1 day'
) RETURNING id INTO meeting_id_2;

-- ---------------------------------------------------------------------------
-- Seed Transcript Segments (for completed meeting)
-- ---------------------------------------------------------------------------

INSERT INTO transcript_segments (meeting_id, speaker_label, start_time, end_time, text, confidence) VALUES
    (meeting_id_1, 'SPEAKER_00', 0.0, 5.2, 'Good morning everyone, let us get started with the standup.', 0.95),
    (meeting_id_1, 'SPEAKER_01', 5.5, 12.8, 'Yesterday I finished the authentication module and started on the API endpoints.', 0.92),
    (meeting_id_1, 'SPEAKER_00', 13.0, 18.5, 'Great progress. Any blockers?', 0.97),
    (meeting_id_1, 'SPEAKER_01', 19.0, 28.3, 'I need access to the staging database. Can someone from DevOps help me with that?', 0.91),
    (meeting_id_1, 'SPEAKER_02', 29.0, 38.5, 'I can set that up for you after this meeting. Should take about ten minutes.', 0.93),
    (meeting_id_1, 'SPEAKER_00', 39.0, 45.2, 'Perfect. Sarah, what about the frontend?', 0.96),
    (meeting_id_1, 'SPEAKER_03', 46.0, 58.8, 'The dashboard is about seventy percent done. I should have the first version ready by Thursday.', 0.90),
    (meeting_id_1, 'SPEAKER_00', 59.0, 68.5, 'Sounds good. Let us plan the demo for Friday then. I will send out the calendar invite.', 0.94);

-- ---------------------------------------------------------------------------
-- Seed Meeting Summary (for completed meeting)
-- ---------------------------------------------------------------------------

INSERT INTO meeting_summaries (meeting_id, summary, action_items, decisions, follow_ups) VALUES (
    meeting_id_1,
    'The weekly standup covered progress on Sprint 12. The authentication module has been completed and API endpoint work has begun. The frontend dashboard is approximately 70% complete with a Thursday target. A product demo is planned for Friday.',
    '[{"task": "Set up staging database access", "assignee": "SPEAKER_02", "deadline": "Today", "priority": "high"}, {"task": "Complete dashboard v1", "assignee": "SPEAKER_03", "deadline": "Thursday", "priority": "high"}, {"task": "Send demo calendar invite", "assignee": "SPEAKER_00", "deadline": "Today", "priority": "medium"}]'::jsonb,
    '[{"decision": "Schedule product demo for Friday", "context": "Dashboard expected to be ready by Thursday", "made_by": "SPEAKER_00", "timestamp": "59.0s - 68.5s"}]'::jsonb,
    '[{"item": "Check dashboard completion status", "owner": "SPEAKER_00", "due": "Thursday", "type": "check_in"}]'::jsonb
);

-- ---------------------------------------------------------------------------
-- Seed BYOM Config
-- ---------------------------------------------------------------------------

INSERT INTO byom_configs (organization_id, provider, model_name, is_active) VALUES
    (org_id, 'openai', 'gpt-4o-mini', true);

-- ---------------------------------------------------------------------------
-- Seed Webhook
-- ---------------------------------------------------------------------------

INSERT INTO webhooks (organization_id, url, events) VALUES
    (org_id, 'https://example.com/webhooks/vaktram', ARRAY['meeting.completed', 'transcription.completed']);

END $$;
