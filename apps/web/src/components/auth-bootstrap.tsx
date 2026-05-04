"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { bootstrapSession } from "@/lib/api/client";
import { useAuthStore } from "@/lib/stores/auth-store";

/**
 * Client-side auth gate for dashboard routes. We can't rely on the edge
 * middleware here because the auth cookies live on the API origin (Render),
 * not the Vercel origin — the Next.js middleware can't read them. So this
 * component fires `bootstrapSession()` (an /auth/refresh) on mount; if the
 * server has no valid refresh cookie, the helper clears local state and we
 * push to /login. While the request is in flight we render a loader so the
 * user never sees a flash of unauthenticated dashboard.
 */
export function AuthBootstrap({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [ready, setReady] = useState(Boolean(accessToken));

  useEffect(() => {
    if (accessToken) {
      setReady(true);
      return;
    }
    let cancelled = false;
    (async () => {
      const token = await bootstrapSession();
      if (cancelled) return;
      if (!token) {
        router.replace("/login");
        return;
      }
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  return <>{children}</>;
}
