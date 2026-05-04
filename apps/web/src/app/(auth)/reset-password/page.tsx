"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { CheckCircle2, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const resetToken = searchParams.get("token") || "";

  const submit = async () => {
    setError(null);

    if (!password) {
      setError("Please enter a new password.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (!resetToken) {
      setError("Invalid or missing reset token.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: resetToken, new_password: password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setError(err.detail || "Something went wrong.");
      } else {
        setSuccess(true);
        toast({
          title: "Password updated",
          description: "You can now sign in with your new password.",
        });
        setTimeout(() => router.push("/login"), 2000);
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="space-y-6">
        <header className="space-y-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-teal-50 text-teal-700">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">
            Password updated
          </h2>
          <p className="text-sm text-slate-600">
            Redirecting you to sign in…
          </p>
        </header>
        <p className="border-t border-slate-100 pt-5">
          <Link
            href="/login"
            className="text-sm font-semibold text-slate-900 hover:underline underline-offset-2"
          >
            Sign in now →
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          Set a new password
        </h2>
        <p className="text-sm text-slate-500">
          Pick something you don&apos;t already use elsewhere.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      <form
        className="space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <div className="space-y-1.5">
          <Label
            htmlFor="password"
            className="text-xs font-medium uppercase tracking-wider text-slate-600"
          >
            New password
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="At least 8 characters"
            className="h-11 rounded-md border-slate-200 bg-white text-[15px] focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            autoComplete="new-password"
            autoFocus
          />
        </div>

        <div className="space-y-1.5">
          <Label
            htmlFor="confirmPassword"
            className="text-xs font-medium uppercase tracking-wider text-slate-600"
          >
            Confirm password
          </Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="Repeat your password"
            className="h-11 rounded-md border-slate-200 bg-white text-[15px] focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading}
            autoComplete="new-password"
          />
        </div>

        <Button
          type="submit"
          className="h-11 w-full rounded-md bg-slate-950 text-[15px] font-semibold text-white shadow-sm transition-all hover:bg-slate-800 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Updating…
            </>
          ) : (
            "Update password"
          )}
        </Button>
      </form>

      <p className="border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
        <Link href="/login" className="font-semibold text-slate-900 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
