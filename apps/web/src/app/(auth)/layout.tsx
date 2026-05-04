"use client";

import { useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Brain, Calendar, Search } from "lucide-react";

// Marketing surface lives at a separate origin (apps/website). The "Home"
// link from auth pages goes there, not to a stub on app.vaktram.com.
const WEBSITE_URL =
  process.env.NEXT_PUBLIC_WEBSITE_URL || "https://vaktram.com";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Auth pages always render in light mode regardless of system preference.
  useEffect(() => {
    document.documentElement.classList.remove("dark");
    document.documentElement.style.colorScheme = "light";
    return () => {
      document.documentElement.style.colorScheme = "";
    };
  }, []);

  return (
    <div className="relative min-h-screen bg-white lg:grid lg:grid-cols-[1.05fr_1fr]">
      {/* ── Brand panel (lg+ only) ───────────────────────────────── */}
      <aside className="relative hidden overflow-hidden bg-slate-950 text-white lg:flex lg:flex-col lg:justify-between lg:px-12 lg:py-10 xl:px-16">
        {/* gradient wash */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(120% 80% at 0% 0%, rgba(15,118,110,0.55) 0%, rgba(15,23,42,0) 60%), radial-gradient(80% 60% at 100% 100%, rgba(20,184,166,0.35) 0%, rgba(15,23,42,0) 55%)",
          }}
        />
        {/* fine grid */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.6) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        {/* top: wordmark */}
        <div className="relative z-10 flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-gradient-to-br from-teal-400 to-teal-600 text-base font-bold text-slate-950 shadow-[inset_0_-4px_12px_rgba(15,23,42,0.25)]">
            V
          </span>
          <span className="text-lg font-semibold tracking-tight">Vaktram</span>
        </div>

        {/* middle: pitch */}
        <div className="relative z-10 max-w-lg">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-300/80">
            Bring your own model
          </p>
          <h1 className="mt-4 text-balance text-4xl font-bold leading-[1.1] tracking-tight xl:text-[2.75rem]">
            Meeting notes on
            <br />
            <span className="bg-gradient-to-r from-teal-200 to-teal-400 bg-clip-text text-transparent">
              the model you choose.
            </span>
          </h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-slate-300">
            Vaktram joins your Google Meet, Zoom, and Teams calls, transcribes
            them, and summarises with the LLM provider <em>you</em> control —
            Gemini, OpenAI, Claude, Mistral, anything LiteLLM-compatible.
          </p>

          <ul className="mt-8 space-y-3.5 text-sm text-slate-200">
            <FeatureRow icon={<Brain className="h-4 w-4" />}>
              Your API keys, your data, your model choice.
            </FeatureRow>
            <FeatureRow icon={<Calendar className="h-4 w-4" />}>
              Auto-joins meetings from your connected calendar.
            </FeatureRow>
            <FeatureRow icon={<Search className="h-4 w-4" />}>
              Searchable transcripts, summaries, and action items.
            </FeatureRow>
          </ul>
        </div>

        {/* bottom: small print */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-400">
          <span>&copy; {new Date().getFullYear()} Vaktram. All rights reserved.</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-400" />
            Built in India
          </span>
        </div>
      </aside>

      {/* ── Form panel ──────────────────────────────────────────── */}
      <main className="relative flex min-h-screen flex-col">
        {/* mobile-only ambient backdrop, mirrors the brand panel hue */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 lg:hidden"
        >
          <div className="absolute -top-32 right-0 h-[420px] w-[420px] rounded-full bg-teal-50 blur-[110px]" />
          <div className="absolute bottom-0 left-0 h-[320px] w-[320px] rounded-full bg-amber-50/60 blur-[110px]" />
        </div>

        {/* top bar: back link (always) + mobile wordmark */}
        <div className="relative z-10 flex items-center justify-between px-4 pt-5 sm:px-8 sm:pt-6">
          <a
            href={WEBSITE_URL}
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-900"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Home
          </a>
          <div className="flex items-center gap-2 lg:invisible">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-950 text-xs font-bold text-white">
              V
            </span>
            <span className="text-sm font-semibold tracking-tight text-slate-900">
              Vaktram
            </span>
          </div>
        </div>

        {/* form */}
        <div className="relative z-10 flex flex-1 items-center justify-center px-4 py-10 sm:px-8">
          <div className="w-full max-w-md">{children}</div>
        </div>

        {/* footer (mobile only — desktop has it in the brand panel) */}
        <p className="relative z-10 pb-6 text-center text-xs text-slate-400 lg:hidden">
          &copy; {new Date().getFullYear()} Vaktram
        </p>
      </main>
    </div>
  );
}

function FeatureRow({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <li className="flex items-start gap-3">
      <span className="mt-0.5 flex h-6 w-6 flex-none items-center justify-center rounded-md border border-white/10 bg-white/5 text-teal-300">
        {icon}
      </span>
      <span className="leading-relaxed">{children}</span>
    </li>
  );
}
