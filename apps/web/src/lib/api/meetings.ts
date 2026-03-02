import { api } from "./client";
import type {
  Meeting,
  CreateMeetingInput,
  TranscriptSegment,
  MeetingSummary,
  SearchResult,
} from "@/types";

export async function getMeetings(params?: {
  status?: string;
  page?: number;
  limit?: number;
}): Promise<Meeting[]> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.limit) searchParams.set("limit", String(params.limit));

  const query = searchParams.toString();
  return api.get<Meeting[]>(`/api/meetings${query ? `?${query}` : ""}`);
}

export async function getMeeting(id: string): Promise<Meeting> {
  return api.get<Meeting>(`/api/meetings/${id}`);
}

export async function createMeeting(
  data: CreateMeetingInput
): Promise<Meeting> {
  return api.post<Meeting>("/api/meetings", data);
}

export async function deleteMeeting(id: string): Promise<void> {
  return api.delete<void>(`/api/meetings/${id}`);
}

export async function getTranscript(
  meetingId: string
): Promise<TranscriptSegment[]> {
  return api.get<TranscriptSegment[]>(
    `/api/meetings/${meetingId}/transcript`
  );
}

export async function getSummary(
  meetingId: string
): Promise<MeetingSummary> {
  return api.get<MeetingSummary>(`/api/meetings/${meetingId}/summary`);
}

export async function startBot(
  meetingId: string
): Promise<{ status: string }> {
  return api.post<{ status: string }>(
    `/api/meetings/${meetingId}/bot/start`
  );
}

export async function stopBot(
  meetingId: string
): Promise<{ status: string }> {
  return api.post<{ status: string }>(
    `/api/meetings/${meetingId}/bot/stop`
  );
}

export async function searchMeetings(
  query: string
): Promise<SearchResult[]> {
  return api.get<SearchResult[]>(
    `/api/meetings/search?q=${encodeURIComponent(query)}`
  );
}
