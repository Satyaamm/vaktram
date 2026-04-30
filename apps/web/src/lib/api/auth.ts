const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
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
  };
}

export interface SignupResult {
  user_id: string;
  email: string;
  organization_id: string;
  verification_email_sent: boolean;
  message: string;
}

/** Server detail can be a string OR a structured object {error, message, ...} */
function extractError(payload: unknown): { code: string | null; message: string } {
  const detail = (payload as { detail?: unknown })?.detail;
  if (typeof detail === "string") return { code: null, message: detail };
  if (detail && typeof detail === "object") {
    const d = detail as { error?: string; message?: string };
    return { code: d.error ?? null, message: d.message ?? "Request failed" };
  }
  return { code: null, message: "Request failed" };
}

export class AuthError extends Error {
  constructor(public status: number, public code: string | null, message: string) {
    super(message);
    this.name = "AuthError";
  }
}

export async function signup(data: {
  full_name: string;
  organization_name: string;
  email: string;
  phone?: string;
  password: string;
  password_confirm: string;
}): Promise<SignupResult> {
  const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const { code, message } = extractError(payload);
    throw new AuthError(res.status, code, message);
  }
  return payload as AuthTokens;
}

export async function refreshTokens(refresh_token: string): Promise<AuthTokens> {
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  if (!res.ok) {
    throw new Error("Session expired");
  }
  return res.json();
}
