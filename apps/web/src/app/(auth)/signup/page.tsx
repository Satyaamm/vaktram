"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle2, Eye, EyeOff, Key, Loader2, MailCheck } from "lucide-react";
import { signup, AuthError } from "@/lib/api/auth";

// Marketing site lives at a separate domain (apps/website). Legal pages
// linked from auth flows resolve there.
const WEBSITE_URL =
  process.env.NEXT_PUBLIC_WEBSITE_URL || "https://vaktram.com";

// Client-side validation mirrors the server's Pydantic rules. The server
// remains the source of truth — these checks just provide instant feedback.
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
      <div className="space-y-6">
        <header className="space-y-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-teal-50 text-teal-700">
            <MailCheck className="h-6 w-6" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">
            Check your email
          </h2>
          <p className="text-sm leading-relaxed text-slate-600">
            We sent a verification link to{" "}
            <span className="font-medium text-slate-900">{done.email}</span>.
            Click it to activate your account — the link expires in 24 hours.
          </p>
        </header>

        <div className="rounded-md border border-amber-200 bg-amber-50 px-3.5 py-3 text-sm text-amber-900">
          <div className="flex gap-2">
            <Key className="mt-0.5 h-4 w-4 flex-none" />
            <p className="leading-relaxed">
              <span className="font-semibold">Heads up:</span> after verifying,
              you&apos;ll add your own LLM API key (Gemini, OpenAI, Claude…)
              before you can use Vaktram. We don&apos;t bundle a model.
            </p>
          </div>
        </div>

        <p className="text-xs text-slate-500">
          Don&apos;t see the email? Check your spam folder, or{" "}
          <Link
            href={`/login?email=${encodeURIComponent(done.email)}`}
            className="font-medium text-slate-900 hover:underline"
          >
            go to sign in
          </Link>{" "}
          to request a new one.
        </p>

        <p className="border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
          Already verified?{" "}
          <Link href="/login" className="font-semibold text-slate-900 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">
          Create your account
        </h2>
        <p className="text-sm text-slate-500">
          Free for your first 10 meetings every month — no card required.
        </p>
      </header>

      {/* BYOM heads-up — unmissable, sets expectations before signup */}
      <div className="rounded-md border border-amber-200 bg-amber-50 px-3.5 py-3 text-sm text-amber-900">
        <div className="flex gap-2">
          <Key className="mt-0.5 h-4 w-4 flex-none" />
          <p className="leading-relaxed">
            <span className="font-semibold">Bring your own model.</span>{" "}
            After verifying your email you&apos;ll connect an LLM API key
            (Gemini, OpenAI, Claude, Mistral…). You stay in control of cost,
            data, and provider.
          </p>
        </div>
      </div>

      {errors._form && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700"
        >
          {errors._form}
        </div>
      )}

      <form
        className="space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <Field label="Full name" htmlFor="full_name" error={fieldError("full_name")}>
          <Input
            id="full_name"
            placeholder="Jane Doe"
            className={fieldClass}
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            onBlur={() => blur("full_name")}
            disabled={loading}
            autoComplete="name"
            autoFocus
          />
        </Field>

        <Field
          label="Organization"
          htmlFor="org"
          error={fieldError("organization_name")}
        >
          <Input
            id="org"
            placeholder="Acme Inc"
            className={fieldClass}
            value={form.organization_name}
            onChange={(e) => set("organization_name", e.target.value)}
            onBlur={() => blur("organization_name")}
            disabled={loading}
            autoComplete="organization"
          />
        </Field>

        <Field label="Work email" htmlFor="email" error={fieldError("email")}>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            className={fieldClass}
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
            placeholder="+91 98765 43210"
            className={fieldClass}
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
              placeholder="At least 8 characters · 1 letter · 1 number"
              className={`${fieldClass} pr-10`}
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              onBlur={() => blur("password")}
              disabled={loading}
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowPwd((s) => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-600"
              aria-label={showPwd ? "Hide password" : "Show password"}
              tabIndex={-1}
            >
              {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {form.password.length > 0 && (
            <div className="mt-2 flex items-center gap-2.5">
              <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-1 transition-all ${strength.color}`}
                  style={{ width: `${strength.pct}%` }}
                />
              </div>
              <span className="w-20 text-right text-xs text-slate-500">
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
          <div className="relative">
            <Input
              id="confirm"
              type={showPwd ? "text" : "password"}
              placeholder="Type it again"
              className={`${fieldClass} pr-10`}
              value={form.password_confirm}
              onChange={(e) => set("password_confirm", e.target.value)}
              onBlur={() => blur("password_confirm")}
              disabled={loading}
              autoComplete="new-password"
            />
            {form.password_confirm.length > 0 &&
              form.password_confirm === form.password && (
                <CheckCircle2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-teal-600" />
              )}
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
              Creating account…
            </>
          ) : (
            "Create account"
          )}
        </Button>

        <p className="text-center text-xs leading-relaxed text-slate-500">
          By creating an account you agree to our{" "}
          <a
            href={`${WEBSITE_URL}/terms`}
            target="_blank"
            rel="noreferrer"
            className="underline hover:text-slate-900"
          >
            Terms
          </a>{" "}
          and{" "}
          <a
            href={`${WEBSITE_URL}/privacy`}
            target="_blank"
            rel="noreferrer"
            className="underline hover:text-slate-900"
          >
            Privacy Policy
          </a>
          .
        </p>
      </form>

      <p className="border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-slate-900 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

const fieldClass =
  "h-11 rounded-md border-slate-200 bg-white text-[15px] focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20";

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
    <div className="space-y-1.5">
      <Label
        htmlFor={htmlFor}
        className="text-xs font-medium uppercase tracking-wider text-slate-600"
      >
        {label}
      </Label>
      {children}
      {error && <p className="mt-0.5 text-xs text-red-600">{error}</p>}
    </div>
  );
}
