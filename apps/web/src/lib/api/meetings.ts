import { api } from "./client";
import type {
  Meeting,
  MeetingList,
  CreateMeetingInput,
  FullTranscript,
  MeetingSummary,
  SearchResult,
} from "@/types";

export async function getMeetings(params?: {
  status?: string;
  page?: number;
  limit?: number;
}): Promise<MeetingList> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.limit) searchParams.set("page_size", String(params.limit));

  const query = searchParams.toString();
  return api.get<MeetingList>(`/api/v1/meetings${query ? `?${query}` : ""}`);
}

export async function getMeeting(id: string): Promise<Meeting> {
  return api.get<Meeting>(`/api/v1/meetings/${id}`);
}

export async function createMeeting(
  data: CreateMeetingInput
): Promise<Meeting> {
  return api.post<Meeting>("/api/v1/meetings", data);
}

export async function deleteMeeting(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/meetings/${id}`);
}

export async function getTranscript(
  meetingId: string
): Promise<FullTranscript> {
  return api.get<FullTranscript>(`/api/v1/transcripts/${meetingId}`);
}

export async function getSummary(
  meetingId: string
): Promise<MeetingSummary> {
  return api.get<MeetingSummary>(`/api/v1/summaries/${meetingId}`);
}

export async function startBot(
  meetingId: string,
  meetingUrl: string
): Promise<{ status: string; meeting_id: string }> {
  return api.post<{ status: string; meeting_id: string }>(
    "/api/v1/bot/join",
    { meeting_id: meetingId, meeting_url: meetingUrl }
  );
}

export async function stopBot(
  meetingId: string
): Promise<{ status: string; meeting_id: string }> {
  return api.post<{ status: string; meeting_id: string }>(
    `/api/v1/bot/leave/${meetingId}`
  );
}

export async function uploadAudio(
  file: File,
  title?: string
): Promise<Meeting> {
  const formData = new FormData();
  formData.append("file", file);
  if (title) formData.append("title", title);
  return api.postForm<Meeting>("/api/v1/meetings/upload-audio", formData);
}

export async function searchMeetings(
  query: string
): Promise<{ results: SearchResult[]; total: number }> {
  return api.post<{ results: SearchResult[]; total: number }>(
    "/api/v1/search",
    { query, top_k: 50 }
  );
}
