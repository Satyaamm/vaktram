import { api } from "./client";

export interface RetentionPolicy {
  default_days: number;
  audio_days: number | null;
  transcript_days: number | null;
  summary_days: number | null;
  legal_hold: boolean;
}

export interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  ip: string | null;
  ts: string;
  details: Record<string, unknown>;
}

export interface AuditChainCheck {
  checked: number;
  breaks: string[];
  ok: boolean;
}

export const complianceApi = {
  getRetention: () => api.get<RetentionPolicy>("/api/v1/compliance/retention"),

  putRetention: (body: Partial<RetentionPolicy>) =>
    api.put<RetentionPolicy>("/api/v1/compliance/retention", body),

  listAudit: (limit = 100) =>
    api.get<AuditEntry[]>(`/api/v1/compliance/audit?limit=${limit}`),

  verifyChain: () =>
    api.get<AuditChainCheck>("/api/v1/compliance/audit/verify"),
};
