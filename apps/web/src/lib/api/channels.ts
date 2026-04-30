import { api } from "./client";

export interface Channel {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_private: boolean;
}

export const channelsApi = {
  list: () => api.get<Channel[]>("/api/v1/channels"),

  create: (body: { name: string; description?: string; is_private?: boolean }) =>
    api.post<{ id: string; slug: string }>("/api/v1/channels", body),

  remove: (id: string) => api.delete<void>(`/api/v1/channels/${id}`),

  addMeeting: (channelId: string, meetingId: string) =>
    api.post<void>(`/api/v1/channels/${channelId}/meetings/${meetingId}`),
};
