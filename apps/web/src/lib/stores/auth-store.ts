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
  accessToken: string | null;
  refreshToken: string | null;
  profile: BackendProfile | null;
  isLoading: boolean;

  setTokens: (accessToken: string, refreshToken: string) => void;
  setProfile: (profile: BackendProfile | null) => void;
  setLoading: (isLoading: boolean) => void;
  clear: () => void;
}

function getStored(key: string): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(key);
}

function getStoredProfile(): BackendProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("vaktram_profile");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: getStored("vaktram_access_token"),
  refreshToken: getStored("vaktram_refresh_token"),
  profile: getStoredProfile(),
  isLoading: true,

  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem("vaktram_access_token", accessToken);
    localStorage.setItem("vaktram_refresh_token", refreshToken);
    // Cookie for Next.js middleware route protection
    document.cookie = `vaktram_token=${accessToken}; path=/; max-age=${60 * 60 * 24}; SameSite=Lax`;
    set({ accessToken, refreshToken });
  },

  setProfile: (profile) => {
    if (profile) {
      localStorage.setItem("vaktram_profile", JSON.stringify(profile));
    } else {
      localStorage.removeItem("vaktram_profile");
    }
    set({ profile });
  },

  setLoading: (isLoading) => set({ isLoading }),

  clear: () => {
    localStorage.removeItem("vaktram_access_token");
    localStorage.removeItem("vaktram_refresh_token");
    localStorage.removeItem("vaktram_profile");
    document.cookie = "vaktram_token=; path=/; max-age=0";
    set({ accessToken: null, refreshToken: null, profile: null, isLoading: false });
  },
}));
