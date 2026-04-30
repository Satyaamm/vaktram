"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader2, MailCheck, UserPlus, Eye, EyeOff } from "lucide-react";
import { signup, AuthError } from "@/lib/api/auth";

// Client-side validation mirrors the server's Pydantic rules. Server is the
// source of truth — these checks just give immediate feedback.
const NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿ'.\- ]+$/;
const PHONE_RE = /^\+?[0-9 ()\-]{7,20}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FormState {
  full_name: string;
  organization_name: string;
  email: string;
  phone: string;
  password: string;
  password_confirm: string;
}

interface FieldErrors extends Partial<Record<keyof FormState, string>> {
  _form?: string;
}

function validate(f: FormState): FieldErrors {
  const e: FieldErrors = {};
  const name = f.full_name.trim();
  if (!name) e.full_name = "Required.";
  else if (name.length < 2) e.full_name = "At least 2 characters.";
  else if (name.length > 100) e.full_name = "Too long.";
  else if (!NAME_RE.test(name))
    e.full_name = "Letters, spaces, apostrophes, hyphens, periods only.";

  const org = f.organization_name.trim();
  if (!org) e.organization_name = "Required.";
  else if (org.length < 2) e.organization_name = "At least 2 characters.";
  else if (org.length > 120) e.organization_name = "Too long.";

  const email = f.email.trim();
  if (!email) e.email = "Required.";
  else if (!EMAIL_RE.test(email)) e.email = "Enter a valid email.";

  const phone = f.phone.trim();
  if (phone && !PHONE_RE.test(phone))
    e.phone = "7–20 digits, optionally with + or spaces.";

  if (!f.password) e.password = "Required.";
  else if (f.password.length < 8) e.password = "At least 8 characters.";
  else if (f.password.length > 128) e.password = "Too long.";
  else if (!/[A-Za-z]/.test(f.password))
    e.password = "Must contain at least one letter.";
  else if (!/[0-9]/.test(f.password))
    e.password = "Must contain at least one number.";

  if (!f.password_confirm) e.password_confirm = "Confirm your password.";
  else if (f.password && f.password_confirm !== f.password)
    e.password_confirm = "Passwords do not match.";

  return e;
}

function passwordStrength(pw: string): { label: string; pct: number; color: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const labels = ["Too weak", "Weak", "Fair", "Good", "Strong", "Excellent"];
  const colors = [
    "bg-red-500",
    "bg-red-500",
    "bg-amber-500",
    "bg-yellow-500",
    "bg-teal-500",
    "bg-teal-700",
  ];
  return { label: labels[score], pct: ((score + 1) / 6) * 100, color: colors[score] };
}

export default function SignupPage() {
  const [form, setForm] = useState<FormState>({
    full_name: "",
    organization_name: "",
    email: "",
    phone: "",
    password: "",
    password_confirm: "",
  });
  const [touched, setTouched] = useState<Partial<Record<keyof FormState, boolean>>>({});
  const [errors, setErrors] = useState<FieldErrors>({});
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState<{ email: string; sent: boolean } | null>(null);

  const liveErrors = useMemo(() => validate(form), [form]);
  const strength = useMemo(() => passwordStrength(form.password), [form.password]);

  const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((f) => ({ ...f, [k]: v }));
  const blur = (k: keyof FormState) => setTouched((t) => ({ ...t, [k]: true }));

  const fieldError = (k: keyof FormState): string | undefined =>
    touched[k] || errors[k] ? liveErrors[k] : undefined;

  const submit = async () => {
    setTouched({
      full_name: true,
      organization_name: true,
      email: true,
      phone: true,
      password: true,
      password_confirm: true,
    });
    const e = validate(form);
    setErrors(e);
    if (Object.keys(e).length > 0) return;

    setLoading(true);
    try {
      const result = await signup({
        full_name: form.full_name.trim(),
        organization_name: form.organization_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        password: form.password,
        password_confirm: form.password_confirm,
      });
      setDone({ email: result.email, sent: result.verification_email_sent });
    } catch (err) {
      if (err instanceof AuthError) {
        if (err.code === "email_exists") {
          setErrors({ email: err.message, _form: err.message });
        } else {
          setErrors({ _form: err.message });
        }
      } else {
        setErrors({ _form: err instanceof Error ? err.message : "Signup failed" });
      }
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-teal-100 text-teal-700">
            <MailCheck className="h-6 w-6" />
          </div>
          <CardTitle className="text-xl font-bold">Check your email</CardTitle>
          <CardDescription className="text-sm">
            We sent a verification link to <b>{done.email}</b>. Click it to
            activate your account — the link expires in 24 hours.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 px-6">
          <p className="text-xs text-muted-foreground text-center">
            Don&apos;t see it? Check spam, or{" "}
            <Link
              href={`/login?email=${encodeURIComponent(done.email)}`}
              className="text-primary hover:underline"
            >
              go to login
            </Link>{" "}
            and request a new link from there.
          </p>
        </CardContent>
        <CardFooter className="justify-center pb-6">
          <p className="text-sm text-muted-foreground">
            Already verified?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full border-slate-200/80 shadow-xl shadow-slate-900/[0.04]">
      <CardHeader className="text-center pb-4">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-base">
          V
        </div>
        <CardTitle className="text-xl font-bold">Create your account</CardTitle>
        <CardDescription className="text-sm">
          Free forever for your first 10 meetings/month.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 px-6">
        {errors._form && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {errors._form}
          </div>
        )}

        <Field label="Full name" htmlFor="full_name" error={fieldError("full_name")}>
          <Input
            id="full_name"
            placeholder="Jane Doe"
            className="h-11 rounded-lg"
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            onBlur={() => blur("full_name")}
            disabled={loading}
            autoComplete="name"
          />
        </Field>

        <Field
          label="Organization name"
          htmlFor="org"
          error={fieldError("organization_name")}
        >
          <Input
            id="org"
            placeholder="Acme Inc"
            className="h-11 rounded-lg"
            value={form.organization_name}
            onChange={(e) => set("organization_name", e.target.value)}
            onBlur={() => blur("organization_name")}
            disabled={loading}
            autoComplete="organization"
          />
        </Field>

        <Field label="Email" htmlFor="email" error={fieldError("email")}>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            className="h-11 rounded-lg"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            onBlur={() => blur("email")}
            disabled={loading}
            autoComplete="email"
          />
        </Field>

        <Field
          label="Phone (optional)"
          htmlFor="phone"
          error={fieldError("phone")}
        >
          <Input
            id="phone"
            type="tel"
            placeholder="+1 415 555 1234"
            className="h-11 rounded-lg"
            value={form.phone}
            onChange={(e) => set("phone", e.target.value)}
            onBlur={() => blur("phone")}
            disabled={loading}
            autoComplete="tel"
          />
        </Field>

        <Field label="Password" htmlFor="password" error={fieldError("password")}>
          <div className="relative">
            <Input
              id="password"
              type={showPwd ? "text" : "password"}
              placeholder="At least 8 characters, 1 letter + 1 number"
              className="h-11 rounded-lg pr-10"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              onBlur={() => blur("password")}
              disabled={loading}
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowPwd((s) => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPwd ? "Hide password" : "Show password"}
              tabIndex={-1}
            >
              {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {form.password.length > 0 && (
            <div className="mt-1.5 flex items-center gap-2">
              <div className="h-1 flex-1 rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-1 transition-all ${strength.color}`}
                  style={{ width: `${strength.pct}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground w-20 text-right">
                {strength.label}
              </span>
            </div>
          )}
        </Field>

        <Field
          label="Confirm password"
          htmlFor="confirm"
          error={fieldError("password_confirm")}
        >
          <Input
            id="confirm"
            type={showPwd ? "text" : "password"}
            placeholder="Type it again"
            className="h-11 rounded-lg"
            value={form.password_confirm}
            onChange={(e) => set("password_confirm", e.target.value)}
            onBlur={() => blur("password_confirm")}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
            disabled={loading}
            autoComplete="new-password"
          />
        </Field>

        <Button
          className="w-full h-11 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground"
          onClick={submit}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <UserPlus className="mr-2 h-4 w-4" />
          )}
          Create account
        </Button>
        <p className="text-xs text-center text-muted-foreground">
          By signing up, you agree to our{" "}
          <Link href="/terms" className="underline hover:text-primary">
            Terms
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="underline hover:text-primary">
            Privacy Policy
          </Link>
          .
        </p>
      </CardContent>
      <CardFooter className="justify-center pb-6">
        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}

function Field({
  label,
  htmlFor,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <Label htmlFor={htmlFor} className="text-sm">
        {label}
      </Label>
      {children}
      {error && <p className="text-xs text-destructive mt-0.5">{error}</p>}
    </div>
  );
}
