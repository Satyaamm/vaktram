import { api } from "./client";

export type PlanTier = "free" | "pro" | "team" | "business" | "enterprise";

export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "canceled"
  | "incomplete"
  | "paused";

export type UsageKind =
  | "transcription_minutes"
  | "llm_input_tokens"
  | "llm_output_tokens"
  | "bot_minutes"
  | "storage_gb_hours"
  | "seats";

export interface PlanCatalogEntry {
  name: string;
  monthly_price_cents: number;
  seat_limit: number;
  features: string[];
  limits: Partial<Record<UsageKind, number>>;
}

export interface Subscription {
  plan: PlanTier;
  status: SubscriptionStatus;
  seats: number;
  trial_ends_at: string | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export interface UsageEntry {
  kind: UsageKind;
  used: number;
  limit: number; // 0 = unlimited
  remaining: number; // -1 = unlimited
}

export interface UsageReport {
  plan: PlanTier;
  period_start: string;
  entries: UsageEntry[];
}

export const billingApi = {
  plans: () => api.get<Record<PlanTier, PlanCatalogEntry>>("/api/v1/billing/plans"),
  subscription: () => api.get<Subscription>("/api/v1/billing/subscription"),
  usage: () => api.get<UsageReport>("/api/v1/billing/usage"),

  checkout: (body: {
    plan: PlanTier;
    seats?: number;
    success_url: string;
    cancel_url: string;
  }) => api.post<{ url: string }>("/api/v1/billing/checkout", body),

  portal: (return_url: string) =>
    api.post<{ url: string }>("/api/v1/billing/portal", { return_url }),
};
