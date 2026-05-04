import { useAuthStore } from "@/lib/stores/auth-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshPromise: Promise<string | null> | null = null;

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return Date.now() >= payload.exp * 1000 - 30_000; // 30s buffer
  } catch {
    return true;
  }
}

/**
 * Hit /auth/refresh; the HttpOnly cookie carries the refresh token, so we
 * send no body. Returns the new access token (in memory only) or null when
 * the user has no valid session and should be sent to /login.
 */
async function tryRefresh(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!res.ok) {
        useAuthStore.getState().clear();
        return null;
      }
      const data = await res.json();
      const store = useAuthStore.getState();
      store.setAccessToken(data.access_token);
      if (data.user) store.setProfile(data.user);
      return data.access_token as string;
    } catch {
      useAuthStore.getState().clear();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

async function getValidAccessToken(): Promise<string | null> {
  const at = useAuthStore.getState().accessToken;
  if (at && !isTokenExpired(at)) return at;
  return tryRefresh();
}

function redirectToLogin() {
  if (typeof window === "undefined") return;
  // Avoid bouncing the auth pages themselves into a redirect loop.
  if (
    /^\/(login|signup|forgot-password|reset-password|verify-email)/.test(
      window.location.pathname,
    )
  )
    return;
  window.location.href = "/login";
}

interface RequestOptions extends RequestInit {
  // Allow callers to opt out of the auto-redirect (e.g. /me on public pages).
  noRedirect?: boolean;
}

async function apiClient<T>(
  endpoint: string,
  options?: RequestOptions,
): Promise<T> {
  const token = await getValidAccessToken();

  const baseHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (token) baseHeaders["Authorization"] = `Bearer ${token}`;

  const doFetch = (headers: Record<string, string>) =>
    fetch(`${API_BASE}${endpoint}`, {
      ...options,
      credentials: "include", // send the HttpOnly refresh cookie too
      headers,
    });

  let response = await doFetch(baseHeaders);

  // One retry on 401: try a refresh and re-request with the new access token.
  if (response.status === 401 && token) {
    const fresh = await tryRefresh();
    if (fresh) {
      const retryHeaders = { ...baseHeaders, Authorization: `Bearer ${fresh}` };
      response = await doFetch(retryHeaders);
    }
    if (response.status === 401) {
      useAuthStore.getState().clear();
      if (!options?.noRedirect) redirectToLogin();
    }
  }

  if (!response.ok) {
    let message = response.statusText;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.message || message;
    } catch {
      // keep statusText
    }
    throw new ApiError(response.status, response.statusText, message);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

async function apiFormData<T>(
  endpoint: string,
  formData: FormData,
): Promise<T> {
  const token = await getValidAccessToken();

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  // Do NOT set Content-Type — the browser sets it with the multipart boundary.

  const doFetch = (h: Record<string, string>) =>
    fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      credentials: "include",
      headers: h,
      body: formData,
    });

  let response = await doFetch(headers);

  if (response.status === 401 && token) {
    const fresh = await tryRefresh();
    if (fresh) {
      response = await doFetch({ ...headers, Authorization: `Bearer ${fresh}` });
    }
    if (response.status === 401) {
      useAuthStore.getState().clear();
      redirectToLogin();
    }
  }

  if (!response.ok) {
    let message = response.statusText;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.message || message;
    } catch {
      // keep statusText
    }
    throw new ApiError(response.status, response.statusText, message);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  get: <T>(url: string, opts?: RequestOptions) => apiClient<T>(url, opts),
  post: <T>(url: string, data?: unknown, opts?: RequestOptions) =>
    apiClient<T>(url, {
      ...opts,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),
  patch: <T>(url: string, data: unknown) =>
    apiClient<T>(url, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  put: <T>(url: string, data: unknown) =>
    apiClient<T>(url, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: <T>(url: string) =>
    apiClient<T>(url, {
      method: "DELETE",
    }),
  postForm: <T>(url: string, formData: FormData) =>
    apiFormData<T>(url, formData),
};

/** Trigger a refresh on app load to bootstrap the access token from cookies. */
export const bootstrapSession = tryRefresh;
