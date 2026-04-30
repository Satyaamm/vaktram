import { api } from "./client";

export interface AiConfigStatus {
  configured: boolean;
  provider: string | null;
  model: string | null;
  is_default?: boolean;
}

export const aiConfigStatusApi = {
  get: () => api.get<AiConfigStatus>("/api/v1/ai-config/status"),
};
