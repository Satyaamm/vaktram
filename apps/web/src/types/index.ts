export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  organization_id: string | null;
  role: string;
  is_active: boolean;
  onboarding_completed: boolean;
  timezone: string | null;
  language: string | null;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  max_seats: number;
  created_at: string;
  updated_at: string;
}

export interface Participant {
  id: string;
  meeting_id: string;
  name: string;
  email: string | null;
  role: string | null;
  speaking_duration_seconds: number | null;
}

export interface Meeting {
  id: string;
  title: string;
  user_id: string;
  organization_id: string | null;
  status: "scheduled" | "in_progress" | "processing" | "transcribing" | "summarizing" | "completed" | "cancelled" | "failed";
  platform: "google_meet" | "zoom" | "teams" | "zoho" | "other";
  meeting_url: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  duration_seconds: number | null;
  bot_id: string | null;
  audio_url: string | null;
  auto_record: boolean;
  transcript_ready: boolean;
  summary_ready: boolean;
  participants: Participant[];
  created_at: string;
  updated_at: string;
}

export interface MeetingList {
  items: Meeting[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateMeetingInput {
  title: string;
  meeting_url?: string;
  platform?: "google_meet" | "zoom" | "teams" | "zoho" | "other";
  scheduled_start?: string;
  scheduled_end?: string;
  auto_record?: boolean;
  participants?: { name: string; email?: string; role?: string }[];
}

export interface TranscriptSegment {
  id: string;
  meeting_id: string;
  speaker_name: string;
  speaker_email: string | null;
  content: string;
  start_time: number;
  end_time: number;
  sequence_number: number;
  confidence: number | null;
  language: string | null;
  created_at: string;
}

export interface FullTranscript {
  meeting_id: string;
  segments: TranscriptSegment[];
  total_segments: number;
}

export interface MeetingSummary {
  id: string;
  meeting_id: string;
  summary_text: string;
  action_items: Record<string, unknown>[] | null;
  key_decisions: Record<string, unknown>[] | null;
  topics: string[] | null;
  sentiment: string | null;
  model_used: string | null;
  provider_used: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  meeting_id: string;
  meeting_title: string;
  segment_id: string;
  speaker_name: string;
  content: string;
  start_time: number;
  end_time: number;
  score: number;
}

export interface CalendarConnection {
  id: string;
  provider: string;
  calendar_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserAIConfig {
  id: string;
  user_id: string;
  provider: string;
  model_name: string;
  has_api_key: boolean;
  base_url: string | null;
  extra_config: Record<string, string> | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
