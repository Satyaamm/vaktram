"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, Loader2, Mail } from "lucide-react";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://app.vaktram.com";
const CONTACT_API = process.env.NEXT_PUBLIC_CONTACT_ENDPOINT || "";

interface FormState {
  name: string;
  email: string;
  company: string;
  team_size: string;
  message: string;
}

const TEAM_SIZES = ["1-10", "11-50", "51-200", "201-1000", "1000+"];

export default function ContactPage() {
  return (
    <main>
      <section className="border-b border-slate-100 py-24">
        <div className="container-wide">
          <div className="grid gap-16 lg:grid-cols-[1fr_1.2fr]">
            <div>
              <p className="eyebrow">Contact</p>
              <h1 className="display mt-3 text-4xl sm:text-5xl">
                Tell us what you're trying to do.
              </h1>
              <p className="mt-5 text-base leading-relaxed text-slate-600">
                Whether you're evaluating Vaktram for a 10-seat team or a
                regulated 500-seat rollout, we'll get back within one business
                day with a real human and concrete answers.
              </p>

              <div className="mt-10 space-y-5 border-t border-slate-100 pt-8">
                <ContactItem
                  icon={<Mail className="h-4 w-4" />}
                  label="Email"
                  value="hello@vaktram.com"
                  href="mailto:hello@vaktram.com"
                />
                <ContactItem
                  label="Already a customer?"
                  value="Sign in to your dashboard"
                  href={`${APP_URL}/login`}
                />
              </div>
            </div>

            <ContactForm />
          </div>
        </div>
      </section>
    </main>
  );
}

function ContactItem({
  icon,
  label,
  value,
  href,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  href: string;
}) {
  return (
    <div>
      <p className="text-[12px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <Link
        href={href}
        className="mt-1 inline-flex items-center gap-2 text-[15px] font-semibold text-slate-900 hover:underline"
      >
        {icon}
        {value}
      </Link>
    </div>
  );
}

function ContactForm() {
  const [form, setForm] = useState<FormState>({
    name: "",
    email: "",
    company: "",
    team_size: "11-50",
    message: "",
  });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((s) => ({ ...s, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.name.trim() || !form.email.trim() || !form.message.trim()) {
      setError("Please fill in name, email, and a short message.");
      return;
    }
    setLoading(true);
    try {
      if (CONTACT_API) {
        const res = await fetch(CONTACT_API, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        });
        if (!res.ok) throw new Error("Send failed");
      } else {
        // Without an endpoint configured, fall back to mailto: so users
        // aren't blocked. Real prod should set NEXT_PUBLIC_CONTACT_ENDPOINT.
        const subject = encodeURIComponent(`Vaktram inquiry from ${form.name}`);
        const body = encodeURIComponent(
          `Name: ${form.name}\nEmail: ${form.email}\nCompany: ${form.company}\nTeam size: ${form.team_size}\n\n${form.message}`,
        );
        window.location.href = `mailto:hello@vaktram.com?subject=${subject}&body=${body}`;
      }
      setDone(true);
    } catch {
      setError("Something went wrong. Please email hello@vaktram.com directly.");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10">
        <div className="flex h-12 w-12 items-center justify-center rounded-md bg-teal-50 text-teal-700">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <h2 className="mt-5 text-2xl font-bold tracking-tight text-slate-900">
          Got it.
        </h2>
        <p className="mt-2 text-base text-slate-600">
          We'll be back to you within one business day. If it's urgent, drop
          a line to{" "}
          <a href="mailto:hello@vaktram.com" className="font-semibold text-slate-900 hover:underline">
            hello@vaktram.com
          </a>
          .
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={submit}
      className="rounded-2xl border border-slate-200 bg-white p-8 sm:p-10"
    >
      {error && (
        <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Name" htmlFor="name">
          <input
            id="name"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            disabled={loading}
            className={fieldClass}
            autoComplete="name"
          />
        </Field>
        <Field label="Work email" htmlFor="email">
          <input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            disabled={loading}
            className={fieldClass}
            autoComplete="email"
          />
        </Field>
        <Field label="Company" htmlFor="company">
          <input
            id="company"
            value={form.company}
            onChange={(e) => set("company", e.target.value)}
            disabled={loading}
            className={fieldClass}
            autoComplete="organization"
          />
        </Field>
        <Field label="Team size" htmlFor="team_size">
          <select
            id="team_size"
            value={form.team_size}
            onChange={(e) => set("team_size", e.target.value)}
            disabled={loading}
            className={fieldClass}
          >
            {TEAM_SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div className="mt-5">
        <Field label="What are you trying to do?" htmlFor="message">
          <textarea
            id="message"
            value={form.message}
            onChange={(e) => set("message", e.target.value)}
            disabled={loading}
            rows={5}
            className={`${fieldClass} resize-none`}
            placeholder="Meeting volume, current notetaker, LLM provider, anything else relevant."
          />
        </Field>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-7 inline-flex h-11 w-full items-center justify-center rounded-md bg-slate-950 text-[15px] font-semibold text-white transition-colors hover:bg-slate-800 disabled:opacity-50 sm:w-auto sm:px-7"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending…
          </>
        ) : (
          "Send"
        )}
      </button>
    </form>
  );
}

const fieldClass =
  "h-11 w-full rounded-md border border-slate-200 bg-white px-3.5 text-[15px] text-slate-900 placeholder:text-slate-400 focus:border-slate-950 focus:outline-none focus:ring-2 focus:ring-slate-950/10";

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={htmlFor}
        className="text-[12px] font-medium uppercase tracking-wider text-slate-600"
      >
        {label}
      </label>
      {children}
    </div>
  );
}
