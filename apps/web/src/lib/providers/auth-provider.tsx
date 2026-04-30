"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";
import { getProfile } from "@/lib/api/settings";
import type { BackendProfile } from "@/lib/stores/auth-store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { accessToken, setProfile, setLoading, clear } = useAuthStore();

  useEffect(() => {
    if (!accessToken) {
      setLoading(false);
      return;
    }

    // Validate token by fetching profile
    getProfile()
      .then((p) => setProfile(p as unknown as BackendProfile))
      .catch(() => {
        // Token invalid or expired and refresh failed
        clear();
      })
      .finally(() => setLoading(false));
  }, [accessToken, setProfile, setLoading, clear]);

  return <>{children}</>;
}
