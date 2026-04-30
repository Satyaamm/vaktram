import { api } from "./client";

export interface Soundbite {
  id: string;
  title: string | null;
  start: number;
  end: number;
  transcript: string | null;
  share_url: string | null;
}

export interface PublicSoundbite {
  title: string | null;
  start: number;
  end: number;
  transcript: string | null;
}

export const soundbitesApi = {
  forMeeting: (meetingId: string) =>
    api.get<Soundbite[]>(`/api/v1/soundbites/by-meeting/${meetingId}`),

  create: (body: {
    meeting_id: string;
    start_seconds: number;
    end_seconds: number;
    title?: string;
    transcript?: string;
  }) =>
    api.post<{ id: string; share_token: string; share_url: string }>(
      "/api/v1/soundbites",
      body,
    ),

  shared: (token: string) =>
    api.get<PublicSoundbite>(`/api/v1/soundbites/shared/${token}`),
};
