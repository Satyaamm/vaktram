import { api } from "./client";
import type { UserProfile, UserAIConfig, CalendarConnection } from "@/types";

// Profile
export async function getProfile(): Promise<UserProfile> {
  return api.get<UserProfile>("/api/v1/teams/profile");
}

export async function updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  return api.patch<UserProfile>("/api/v1/teams/profile", data);
}

// AI Config (BYOM)
export async function getAIConfigs(): Promise<UserAIConfig[]> {
  return api.get<UserAIConfig[]>("/api/v1/ai-config");
}

export async function createAIConfig(data: {
  provider: string;
  model_name: string;
  api_key?: string;
  base_url?: string;
  extra_config?: Record<string, string>;
  is_default?: boolean;
}): Promise<UserAIConfig> {
  return api.post<UserAIConfig>("/api/v1/ai-config", data);
}

export async function updateAIConfig(
  id: string,
  data: Partial<{
    provider: string;
    model_name: string;
    api_key: string;
    base_url: string;
    extra_config: Record<string, string>;
    is_default: boolean;
    is_active: boolean;
  }>
): Promise<UserAIConfig> {
  return api.patch<UserAIConfig>(`/api/v1/ai-config/${id}`, data);
}

export async function deleteAIConfig(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/ai-config/${id}`);
}

export async function testAIConfig(data: {
  provider: string;
  model_name: string;
  api_key?: string;
  base_url?: string;
  extra_config?: Record<string, string>;
}): Promise<{ success: boolean; message: string; response_time_ms?: number }> {
  return api.post("/api/v1/ai-config/test", data);
}

// Calendar
export async function getCalendarConnections(): Promise<CalendarConnection[]> {
  return api.get<CalendarConnection[]>("/api/v1/calendar/connections");
}

export async function authorizeCalendar(): Promise<{ authorization_url: string }> {
  return api.post<{ authorization_url: string }>("/api/v1/calendar/authorize", {});
}

export async function syncCalendar(): Promise<{ synced_count: number; new_meetings: string[] }> {
  return api.post<{ synced_count: number; new_meetings: string[] }>("/api/v1/calendar/sync", {});
}

export async function disconnectCalendar(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/calendar/${id}`);
}

// Analytics
export interface AnalyticsOverview {
  total_meetings: number;
  total_duration_hours: number;
  meetings_this_week: number;
  avg_duration_minutes: number;
}

export interface SpeakerTalkTime {
  speaker_name: string;
  total_seconds: number;
  meeting_count: number;
  percentage: number;
}

export interface MeetingFrequency {
  date: string;
  count: number;
}

export interface TopicFrequency {
  topic: string;
  count: number;
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return api.get<AnalyticsOverview>("/api/v1/analytics/overview");
}

export async function getSpeakerTalkTime(): Promise<SpeakerTalkTime[]> {
  return api.get<SpeakerTalkTime[]>("/api/v1/analytics/talk-time");
}

export async function getMeetingFrequency(period?: string): Promise<MeetingFrequency[]> {
  const query = period ? `?period=${period}` : "";
  return api.get<MeetingFrequency[]>(`/api/v1/analytics/frequency${query}`);
}

export async function getTopicFrequency(): Promise<TopicFrequency[]> {
  return api.get<TopicFrequency[]>("/api/v1/analytics/topics");
}

// Usage / Billing
export interface UsageData {
  meetings_this_month: number;
  storage_used_mb: number;
  plan: string;
}

export async function getUsage(): Promise<UsageData> {
  return api.get<UsageData>("/api/v1/analytics/usage");
}

// Team
export interface TeamMember {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

export async function getTeamMembers(): Promise<TeamMember[]> {
  return api.get<TeamMember[]>("/api/v1/teams/members");
}

export async function inviteTeamMember(email: string, role: string): Promise<void> {
  return api.post<void>("/api/v1/teams/invite", { email, role });
}

export async function updateMemberRole(memberId: string, role: string): Promise<void> {
  return api.patch<void>(`/api/v1/teams/members/${memberId}`, { role });
}

export async function removeMember(memberId: string): Promise<void> {
  return api.delete<void>(`/api/v1/teams/members/${memberId}`);
}

// Notifications
export interface AppNotification {
  id: string;
  title: string;
  body: string | null;
  notification_type: string;
  is_read: boolean;
  link: string | null;
  created_at: string;
}

export async function getNotifications(): Promise<AppNotification[]> {
  return api.get<AppNotification[]>("/api/v1/notifications");
}

export async function markNotificationRead(id: string): Promise<void> {
  return api.patch<void>(`/api/v1/notifications/${id}/read`, {});
}

export async function markAllNotificationsRead(): Promise<void> {
  return api.post<void>("/api/v1/notifications/read-all");
}
