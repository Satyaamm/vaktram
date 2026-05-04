"use client";

import { useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Brain, Calendar, Search } from "lucide-react";

import { Logo } from "@/components/brand/logo";

// Auth chrome — fully light. Split-screen on lg+ with a tinted brand
// panel on the left and the form on the right. Dark CTAs (slate-950)
// are the only "very dark" surface and stand out cleanly against the
// white background.

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Force light theme regardless of system preference.
  useEffect(() => {
    document.documentElement.classList.remove("dark");
    document.documentElement.style.colorScheme = "light";
    return () => {
      document.documentElement.style.colorScheme = "";
    };
  }, []);

  return (
    <div className="relative min-h-screen bg-white text-slate-900 lg:grid lg:grid-cols-[1.05fr_1fr]">
      {/* ── Brand panel (lg+) — tinted light ──────────────────── */}
      <aside className="relative hidden overflow-hidden bg-slate-50 lg:flex lg:flex-col lg:justify-between lg:px-12 lg:py-10 xl:px-16">
        {/* gentle teal+amber gradient wash on a near-white surface */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(120% 80% at 0% 0%, rgba(20,184,166,0.10) 0%, rgba(255,255,255,0) 60%), radial-gradient(70% 50% at 100% 100%, rgba(245,158,11,0.08) 0%, rgba(255,255,255,0) 55%)",
          }}
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-dot-grid opacity-50"
        />

        <Logo variant="long" tone="light" className="relative z-10" />

        <div className="relative z-10 max-w-lg">
          <p className="eyebrow">Bring your own model</p>
          <h1 className="display mt-4 text-balance text-4xl xl:text-[2.75rem]">
            Meeting notes on
            <br />
            <span className="bg-gradient-to-r from-teal-700 to-teal-500 bg-clip-text text-transparent">
              the model you choose.
            </span>
          </h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-slate-600">
            Vaktram joins your Google Meet, Zoom, and Teams calls, transcribes
            them, and summarises with the LLM provider <em>you</em> control —
            Gemini, OpenAI, Claude, Mistral, anything LiteLLM-compatible.
          </p>
          <ul className="mt-8 space-y-3.5 text-sm text-slate-700">
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

        <div className="relative z-10 flex items-center justify-between text-xs text-slate-500">
          <span>&copy; {new Date().getFullYear()} Vaktram. All rights reserved.</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            Built in India
          </span>
        </div>
      </aside>

      {/* ── Form panel — pure white ────────────────────────────── */}
      <main className="relative flex min-h-screen flex-col bg-white lg:border-l lg:border-slate-100">
        <div className="relative z-10 flex items-center justify-between px-4 pt-5 sm:px-8 sm:pt-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-900"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Home
          </Link>
          <div className="lg:invisible">
            <Logo variant="long" tone="light" />
          </div>
        </div>

        <div className="relative z-10 flex flex-1 items-center justify-center px-4 py-10 sm:px-8">
          <div className="w-full max-w-md">{children}</div>
        </div>

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
      <span className="mt-0.5 flex h-6 w-6 flex-none items-center justify-center rounded-md border border-slate-200 bg-white text-teal-700">
        {icon}
      </span>
      <span className="leading-relaxed">{children}</span>
    </li>
  );
}
