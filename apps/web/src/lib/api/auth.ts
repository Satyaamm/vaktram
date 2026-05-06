const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface BackendUser {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  organization_id: string | null;
  organization_name: string | null;
  is_active: boolean;
  onboarding_completed: boolean;
  timezone: string | null;
  language: string | null;
  created_at: string;
  updated_at: string;
}

/** Server response shape: tokens for legacy clients (still returned in body),
 * cookies set as Set-Cookie for the modern path. The frontend reads only
 * `access_token` (kept in memory) and `user`; the refresh token in the body
 * is intentionally ignored — the HttpOnly cookie is the authoritative copy. */
export interface AuthTokens {
  access_token: string;
  refresh_token: string; // ignored by the modern client; cookie is canonical
  token_type: string;
  user: BackendUser;
}

export interface SignupResult {
  user_id: string;
  email: string;
  organization_id: string;
  verification_email_sent: boolean;
  message: string;
}

// Shared error parser handles FastAPI's three detail shapes (string,
// validation list, structured object) without crashing React on render.
import { parseApiError } from "./errors";

const extractError = (payload: unknown) => parseApiError(payload, "Request failed");

export class AuthError extends Error {
  constructor(public status: number, public code: string | null, message: string) {
    super(message);
    this.name = "AuthError";
  }
}

const COMMON: RequestInit = {
  credentials: "include",
  headers: { "Content-Type": "application/json" },
};

export async function signup(data: {
  full_name: string;
  organization_name: string;
  email: string;
  phone?: string;
  password: string;
  password_confirm: string;
}): Promise<SignupResult> {
  const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
    ...COMMON,
    method: "POST",
    body: JSON.stringify(data),
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const { code, message } = extractError(payload);
    throw new AuthError(res.status, code, message);
  }
  return payload as SignupResult;
}

export async function verifyEmail(token: string): Promise<AuthTokens> {
  const res = await fetch(`${API_BASE}/api/v1/auth/verify-email`, {
    ...COMMON,
    method: "POST",
    body: JSON.stringify({ token }),
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const { code, message } = extractError(payload);
    throw new AuthError(res.status, code, message);
  }
  return payload as AuthTokens;
}

export async function resendVerification(email: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/resend-verification`, {
    ...COMMON,
    method: "POST",
    body: JSON.stringify({ email }),
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const { code, message } = extractError(payload);
    throw new AuthError(res.status, code, message);
  }
  return payload as { message: string };
}

export async function login(data: {
  email: string;
  password: string;
}): Promise<AuthTokens> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    ...COMMON,
    method: "POST",
    body: JSON.stringify(data),
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const { code, message } = extractError(payload);
    throw new AuthError(res.status, code, message);
  }
  return payload as AuthTokens;
}

export async function logout(): Promise<void> {
  // Cookie carries the refresh token; we send no body. 204 expected.
  await fetch(`${API_BASE}/api/v1/auth/logout`, {
    ...COMMON,
    method: "POST",
    body: "{}",
  }).catch(() => {
    // Logout is best-effort — UI should clear local state regardless.
  });
}
