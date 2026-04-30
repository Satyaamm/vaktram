-- ============================================
-- Vaktram: RLS Policies
-- ============================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcript_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_ai_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- ============================================
-- USER PROFILES
-- ============================================

-- Users can read their own profile
CREATE POLICY "users_read_own_profile" ON user_profiles
  FOR SELECT USING (id = auth.uid());

-- Users can insert their own profile (for callback route after signup)
CREATE POLICY "users_insert_own_profile" ON user_profiles
  FOR INSERT WITH CHECK (id = auth.uid());

-- Users can update their own profile
CREATE POLICY "users_update_own_profile" ON user_profiles
  FOR UPDATE USING (id = auth.uid());

-- ============================================
-- MEETINGS
-- ============================================

-- Users can read their own meetings
CREATE POLICY "users_read_own_meetings" ON meetings
  FOR SELECT USING (user_id = auth.uid());

-- Users can create meetings
CREATE POLICY "users_create_meetings" ON meetings
  FOR INSERT WITH CHECK (user_id = auth.uid());

-- Users can update their own meetings
CREATE POLICY "users_update_own_meetings" ON meetings
  FOR UPDATE USING (user_id = auth.uid());

-- Users can delete their own meetings
CREATE POLICY "users_delete_own_meetings" ON meetings
  FOR DELETE USING (user_id = auth.uid());

-- ============================================
-- MEETING PARTICIPANTS
-- ============================================

-- Users can read participants of their own meetings
CREATE POLICY "users_read_meeting_participants" ON meeting_participants
  FOR SELECT USING (
    meeting_id IN (SELECT id FROM meetings WHERE user_id = auth.uid())
  );

-- ============================================
-- TRANSCRIPT SEGMENTS
-- ============================================

-- Users can read transcripts of their own meetings
CREATE POLICY "users_read_own_transcripts" ON transcript_segments
  FOR SELECT USING (
    meeting_id IN (SELECT id FROM meetings WHERE user_id = auth.uid())
  );

-- ============================================
-- MEETING SUMMARIES
-- ============================================

-- Users can read summaries of their own meetings
CREATE POLICY "users_read_own_summaries" ON meeting_summaries
  FOR SELECT USING (
    meeting_id IN (SELECT id FROM meetings WHERE user_id = auth.uid())
  );

-- ============================================
-- USER AI CONFIGS (BYOM)
-- ============================================

-- Users can CRUD their own AI configs
CREATE POLICY "users_manage_own_ai_configs" ON user_ai_configs
  FOR ALL USING (user_id = auth.uid());

-- ============================================
-- CALENDAR CONNECTIONS
-- ============================================

-- Users can CRUD their own calendar connections
CREATE POLICY "users_manage_own_calendars" ON calendar_connections
  FOR ALL USING (user_id = auth.uid());

-- ============================================
-- NOTIFICATIONS
-- ============================================

-- Users can read their own notifications
CREATE POLICY "users_read_own_notifications" ON notifications
  FOR SELECT USING (user_id = auth.uid());

-- Users can update their own notifications (mark read)
CREATE POLICY "users_update_own_notifications" ON notifications
  FOR UPDATE USING (user_id = auth.uid());

-- ============================================
-- API KEYS
-- ============================================

-- Users can CRUD their own API keys
CREATE POLICY "users_manage_own_api_keys" ON api_keys
  FOR ALL USING (user_id = auth.uid());

-- ============================================
-- MEETING EMBEDDINGS
-- ============================================

-- Users can read embeddings of their own meetings
CREATE POLICY "users_read_own_embeddings" ON meeting_embeddings
  FOR SELECT USING (
    meeting_id IN (SELECT id FROM meetings WHERE user_id = auth.uid())
  );
