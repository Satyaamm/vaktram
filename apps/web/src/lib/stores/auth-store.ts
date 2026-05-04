import { create } from "zustand";

export interface BackendProfile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  organization_id: string | null;
  organization_name: string | null;
  role: string;
  is_active: boolean;
  onboarding_completed: boolean;
  timezone: string | null;
  language: string | null;
}

interface AuthState {
  // Access token lives in JS memory only — never persisted. An XSS payload
  // can still steal it from this store while it's loaded, but it expires in
  // 15 minutes and the refresh token is HttpOnly, so the attacker can't
  // mint new ones.
  accessToken: string | null;

  // Profile is non-credential and used for UI hints; persisted to
  // localStorage so a page reload doesn't flash an unauthenticated UI
  // before /refresh + /me complete.
  profile: BackendProfile | null;

  isLoading: boolean;

  setAccessToken: (token: string | null) => void;
  setProfile: (profile: BackendProfile | null) => void;
  setLoading: (isLoading: boolean) => void;
  clear: () => void;
}

const PROFILE_KEY = "vaktram_profile";

function getStoredProfile(): BackendProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  profile: getStoredProfile(),
  isLoading: true,

  setAccessToken: (accessToken) => set({ accessToken }),

  setProfile: (profile) => {
    if (typeof window !== "undefined") {
      if (profile) {
        localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
      } else {
        localStorage.removeItem(PROFILE_KEY);
      }
    }
    set({ profile });
  },

  setLoading: (isLoading) => set({ isLoading }),

  clear: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(PROFILE_KEY);
      // Legacy keys from the pre-cookie era — clear them once and they're
      // gone for good.
      localStorage.removeItem("vaktram_access_token");
      localStorage.removeItem("vaktram_refresh_token");
    }
    set({ accessToken: null, profile: null, isLoading: false });
  },
}));
