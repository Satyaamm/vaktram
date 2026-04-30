import { useAuthStore } from "@/lib/stores/auth-store";
import { refreshTokens } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string
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

async function tryRefresh(): Promise<string | null> {
  const store = useAuthStore.getState();
  const rt = store.refreshToken;
  if (!rt) {
    store.clear();
    return null;
  }

  // Deduplicate concurrent refresh calls
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const tokens = await refreshTokens(rt);
        store.setTokens(tokens.access_token, tokens.refresh_token);
        store.setProfile(tokens.user);
        return tokens.access_token;
      } catch {
        // Refresh token is invalid/expired → force logout
        store.clear();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }

  return refreshPromise;
}

async function getValidAccessToken(): Promise<string | null> {
  const store = useAuthStore.getState();
  const at = store.accessToken;

  // If access token exists and not expired, use it
  if (at && !isTokenExpired(at)) {
    return at;
  }

  // Otherwise try to refresh
  return tryRefresh();
}

async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = await getValidAccessToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options?.headers || {}),
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // If 401, try refresh once and retry the request
  if (response.status === 401 && token) {
    const newToken = await tryRefresh();
    if (newToken) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${newToken}`;
      const retry = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });
      if (retry.ok) {
        if (retry.status === 204) return undefined as T;
        return retry.json();
      }
      // Retry also failed — fall through to error handling below
      if (retry.status === 401) {
        useAuthStore.getState().clear();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
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

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

async function apiFormData<T>(
  endpoint: string,
  formData: FormData,
): Promise<T> {
  const token = await getValidAccessToken();

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  // Do NOT set Content-Type — browser sets it with boundary for multipart

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (response.status === 401 && token) {
    const newToken = await tryRefresh();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      const retry = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers,
        body: formData,
      });
      if (retry.ok) {
        if (retry.status === 204) return undefined as T;
        return retry.json();
      }
      if (retry.status === 401) {
        useAuthStore.getState().clear();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
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
  get: <T>(url: string) => apiClient<T>(url),
  post: <T>(url: string, data?: unknown) =>
    apiClient<T>(url, {
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
