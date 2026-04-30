import { api } from "./client";

export interface TopicTracker {
  id: string;
  name: string;
  keywords: string[];
  is_active: boolean;
  notify_emails: string[];
}

export interface TopicHit {
  id: string;
  meeting_id: string;
  matched_keyword: string;
  snippet: string;
  timestamp: number | null;
  created_at: string;
}

export const topicsApi = {
  list: () => api.get<TopicTracker[]>("/api/v1/topics"),

  create: (body: { name: string; keywords: string[]; notify_emails?: string[] }) =>
    api.post<{ id: string }>("/api/v1/topics", body),

  update: (
    id: string,
    body: Partial<{
      name: string;
      keywords: string[];
      notify_emails: string[];
      is_active: boolean;
    }>,
  ) => api.patch<{ ok: true }>(`/api/v1/topics/${id}`, body),

  remove: (id: string) => api.delete<void>(`/api/v1/topics/${id}`),

  hits: (id: string) => api.get<TopicHit[]>(`/api/v1/topics/${id}/hits`),
};
