"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { verifyEmail, AuthError } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/auth-store";

type Status = "loading" | "success" | "error";

// useSearchParams forces client-side rendering. App Router needs that piece
// wrapped in a Suspense boundary so the rest of the route can pre-render.
export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<VerifyEmailSkeleton />}>
      <VerifyEmailInner />
    </Suspense>
  );
}

function VerifyEmailSkeleton() {
  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-md bg-slate-100 text-slate-500">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          Verifying your email…
        </h2>
      </header>
    </div>
  );
}

function VerifyEmailInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");

  const { setAccessToken, setProfile } = useAuthStore();
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("This verification link is missing a token.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const tokens = await verifyEmail(token);
        if (cancelled) return;
        setAccessToken(tokens.access_token);
        setProfile(tokens.user);
        setStatus("success");
        // Land brand-new users on AI config (BYOM is required to use anything),
        // not the empty dashboard.
        setTimeout(
          () => router.push("/settings/ai-config?from=verify"),
          1200,
        );
      } catch (e) {
        if (cancelled) return;
        setStatus("error");
        setError(
          e instanceof AuthError
            ? e.message
            : e instanceof Error
              ? e.message
              : "Verification failed.",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, router, setAccessToken, setProfile]);

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        {status === "loading" && (
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-slate-100 text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        )}
        {status === "success" && (
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-teal-50 text-teal-700">
            <CheckCircle2 className="h-6 w-6" />
          </div>
        )}
        {status === "error" && (
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-amber-50 text-amber-700">
            <AlertTriangle className="h-6 w-6" />
          </div>
        )}
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          {status === "loading" && "Verifying your email…"}
          {status === "success" && "Email verified"}
          {status === "error" && "Verification failed"}
        </h2>
        <p className="text-sm leading-relaxed text-slate-600">
          {status === "loading" && "Hold tight, this only takes a moment."}
          {status === "success" &&
            "Welcome to Vaktram. Taking you to add your LLM key…"}
          {status === "error" && error}
        </p>
      </header>

      {status === "error" && (
        <>
          <p className="text-sm text-slate-500">
            If the link expired, head back to sign in and request a fresh
            verification email from there.
          </p>
          <div className="flex gap-2 pt-2">
            <Link href="/login" className="flex-1">
              <Button
                variant="outline"
                className="h-11 w-full rounded-md border-slate-200"
              >
                Go to sign in
              </Button>
            </Link>
            <Link href="/signup" className="flex-1">
              <Button className="h-11 w-full rounded-md bg-slate-950 hover:bg-slate-800">
                Sign up again
              </Button>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
