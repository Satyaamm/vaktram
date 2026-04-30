import { api } from "./client";

export type AskScope = "meeting" | "channel" | "organization";

export interface AskCitation {
  meeting_id: string;
  segment_id: string | null;
  meeting_title: string | null;
  content: string;
  speaker_name: string | null;
  start_time: number | null;
  score: number;
}

export interface AskMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: AskCitation[];
  created_at?: string;
}

export interface AskThreadSummary {
  id: string;
  title: string | null;
  scope: AskScope;
  created_at?: string;
}

export interface AskThread {
  id: string;
  title: string | null;
  scope: AskScope;
  scope_id: string | null;
  messages: AskMessage[];
}

export const askApi = {
  listThreads: () => api.get<AskThreadSummary[]>("/api/v1/ask/threads"),

  getThread: (id: string) => api.get<AskThread>(`/api/v1/ask/threads/${id}`),

  createThread: (body: { title?: string; scope?: AskScope; scope_id?: string }) =>
    api.post<{ id: string; title: string | null; scope: AskScope }>(
      "/api/v1/ask/threads",
      body,
    ),

  send: (threadId: string, message: string) =>
    api.post<AskMessage>(`/api/v1/ask/threads/${threadId}/messages`, { message }),
};
