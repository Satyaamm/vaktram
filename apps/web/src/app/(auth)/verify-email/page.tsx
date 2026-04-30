"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Loader2, AlertTriangle } from "lucide-react";
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
    <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
      <CardHeader className="text-center pb-4">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
        <CardTitle className="text-xl font-bold">Verifying your email…</CardTitle>
      </CardHeader>
    </Card>
  );
}

function VerifyEmailInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");

  const { setTokens, setProfile } = useAuthStore();
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
        setTokens(tokens.access_token, tokens.refresh_token);
        setProfile(tokens.user);
        setStatus("success");
        setTimeout(() => router.push("/dashboard"), 1200);
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
  }, [token, router, setTokens, setProfile]);

  return (
    <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
      <CardHeader className="text-center pb-4">
        {status === "loading" && (
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {status === "success" && (
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-teal-100 text-teal-700">
            <CheckCircle2 className="h-6 w-6" />
          </div>
        )}
        {status === "error" && (
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-amber-700">
            <AlertTriangle className="h-6 w-6" />
          </div>
        )}
        <CardTitle className="text-xl font-bold">
          {status === "loading" && "Verifying your email…"}
          {status === "success" && "Email verified"}
          {status === "error" && "Verification failed"}
        </CardTitle>
        <CardDescription className="text-sm">
          {status === "loading" && "Hold tight, this only takes a moment."}
          {status === "success" && "Welcome to Vaktram. Redirecting to your dashboard…"}
          {status === "error" && error}
        </CardDescription>
      </CardHeader>
      {status === "error" && (
        <>
          <CardContent className="px-6">
            <p className="text-sm text-muted-foreground">
              If the link expired, return to the login page and request a fresh
              verification email.
            </p>
          </CardContent>
          <CardFooter className="flex justify-center gap-2 pb-6">
            <Link href="/login">
              <Button variant="outline">Go to login</Button>
            </Link>
            <Link href="/signup">
              <Button>Sign up again</Button>
            </Link>
          </CardFooter>
        </>
      )}
    </Card>
  );
}
