export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  organization_id: string | null;
  role: "owner" | "admin" | "member" | "viewer";
  plan: "free" | "pro" | "team" | "enterprise";
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  plan: "free" | "pro" | "team" | "enterprise";
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface Participant {
  id: string;
  meeting_id: string;
  user_id: string | null;
  name: string;
  email: string | null;
  role: "host" | "participant" | "guest";
  talk_time_seconds: number;
  joined_at: string;
  left_at: string | null;
}

export interface Meeting {
  id: string;
  title: string;
  description: string | null;
  organizer_id: string;
  organization_id: string | null;
  status: "scheduled" | "in_progress" | "completed" | "cancelled";
  platform: "zoom" | "google_meet" | "teams" | "other";
  meeting_url: string | null;
  recording_url: string | null;
  duration_seconds: number | null;
  participant_count: number;
  participants: Participant[];
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranscriptSegment {
  id: string;
  meeting_id: string;
  speaker_id: string | null;
  speaker_name: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  language: string;
}

export interface MeetingSummary {
  id: string;
  meeting_id: string;
  summary: string;
  key_topics: string[];
  action_items: ActionItem[];
  decisions: string[];
  sentiment: "positive" | "neutral" | "negative" | "mixed";
  llm_provider: string;
  llm_model: string;
  generated_at: string;
}

export interface ActionItem {
  id: string;
  meeting_id: string;
  title: string;
  description: string | null;
  assignee_id: string | null;
  assignee_name: string | null;
  due_date: string | null;
  status: "pending" | "in_progress" | "completed";
  priority: "low" | "medium" | "high";
  created_at: string;
}

export interface CreateMeetingInput {
  title: string;
  description?: string;
  platform: "zoom" | "google_meet" | "teams" | "other";
  meeting_url?: string;
  scheduled_at?: string;
}

export interface SearchResult {
  meeting_id: string;
  meeting_title: string;
  segment_id: string;
  speaker_name: string;
  text: string;
  start_time: number;
  end_time: number;
  score: number;
}

export interface CalendarConnection {
  id: string;
  provider: "google" | "outlook";
  calendar_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface UserAIConfig {
  id: string;
  user_id: string;
  provider: "openai" | "anthropic" | "google" | "azure" | "ollama" | "custom";
  model: string;
  api_key_encrypted: string;
  base_url: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}
