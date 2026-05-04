"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Loader2 } from "lucide-react";

import { login } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/auth-store";
import { Logo } from "@/components/brand/logo";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();
  const { setAccessToken, setProfile } = useAuthStore();

  const handleLogin = async () => {
    setError(null);
    if (!email.trim()) return setError("Please enter your email address.");
    if (!password) return setError("Please enter your password.");

    setLoading(true);
    try {
      const result = await login({ email: email.trim(), password });
      setAccessToken(result.access_token);
      setProfile(result.user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-9">
      {/* Compact short-mark logo above the form on every viewport */}
      <Logo variant="short" tone="light" href={undefined} />

      <header className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-slate-950">
          Welcome back
        </h2>
        <p className="text-sm text-slate-500">
          Sign in to pick up where you left off.
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
          handleLogin();
        }}
      >
        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            className={fieldClass}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            autoComplete="email"
            autoFocus
          />
        </Field>

        <Field
          label="Password"
          htmlFor="password"
          rightLink={{ label: "Forgot?", href: "/forgot-password" }}
        >
          <div className="relative">
            <Input
              id="password"
              type={showPwd ? "text" : "password"}
              placeholder="Your password"
              className={`${fieldClass} pr-10`}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPwd((s) => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-700"
              aria-label={showPwd ? "Hide password" : "Show password"}
              tabIndex={-1}
            >
              {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </Field>

        <Button
          type="submit"
          className="h-11 w-full rounded-md bg-slate-950 text-[15px] font-semibold text-white shadow-sm transition-all hover:bg-slate-800 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in…
            </>
          ) : (
            "Sign in"
          )}
        </Button>
      </form>

      <p className="border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
        Don't have an account?{" "}
        <Link
          href="/signup"
          className="font-semibold text-slate-950 hover:underline underline-offset-2"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}

const fieldClass =
  "h-11 rounded-md border-slate-200 bg-white text-[15px] text-slate-900 placeholder:text-slate-400 focus-visible:border-slate-950 focus-visible:ring-2 focus-visible:ring-slate-950/10";

function Field({
  label,
  htmlFor,
  rightLink,
  children,
}: {
  label: string;
  htmlFor: string;
  rightLink?: { label: string; href: string };
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <Label
          htmlFor={htmlFor}
          className="text-[12px] font-medium uppercase tracking-wider text-slate-600"
        >
          {label}
        </Label>
        {rightLink && (
          <Link
            href={rightLink.href}
            className="text-[12px] font-medium text-slate-700 hover:text-slate-950 hover:underline underline-offset-2"
          >
            {rightLink.label}
          </Link>
        )}
      </div>
      {children}
    </div>
  );
}
