import Link from "next/link";
import {
  ArrowRight,
  Brain,
  Calendar,
  CheckCircle2,
  Lock,
  Search,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────
// Home page sections — modeled on the Pylon flow:
//   1. Hero with kicker + headline + subhead + dual CTA + product preview
//   2. Logo strip ("Trusted by ...")
//   3. Three-pillar value section
//   4. Feature card grid
//   5. Pipeline visual (meeting → bot → transcript → summary)
//   6. Security band
//   7. Big CTA band
// Copy is Vaktram-native; layout is fresh markup, not scraped from Pylon.
// ─────────────────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <main>
      <Hero />
      <LogoStrip />
      <Pillars />
      <FeatureGrid />
      <Pipeline />
      <SecurityBand />
      <CTABand />
    </main>
  );
}

function Hero() {
  return (
    <section className="relative isolate overflow-hidden">
      {/* Ambient gradient + grid wash */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, rgba(20,184,166,0.08) 0%, transparent 70%)",
        }}
      />
      <div className="pointer-events-none absolute inset-0 bg-dot-grid opacity-60" />

      <div className="container-wide relative pt-20 pb-24 sm:pt-28 sm:pb-32">
        <div className="mx-auto max-w-3xl text-center">
          <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-teal-200/60 bg-teal-50/60 px-3 py-1">
            <Sparkles className="h-3 w-3" />
            Bring your own model
          </span>

          <h1 className="display mt-6 text-[44px] sm:text-6xl xl:text-7xl">
            Meeting notes on
            <br />
            <span className="bg-gradient-to-r from-teal-700 via-teal-500 to-teal-700 bg-clip-text text-transparent">
              the model you choose.
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-balance text-base leading-relaxed text-slate-600 sm:text-lg">
            Vaktram joins your Google Meet, Zoom, and Teams calls, transcribes
            them, and summarises with the LLM provider <em>you</em> control —
            Gemini, OpenAI, Claude, Mistral, anything LiteLLM-compatible. Your
            keys, your data, your spend.
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex items-center gap-1.5 rounded-md bg-slate-950 px-5 py-3 text-[15px] font-semibold text-white shadow-sm transition-all hover:bg-slate-800"
            >
              Start free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md border border-slate-200 bg-white px-5 py-3 text-[15px] font-semibold text-slate-900 transition-colors hover:bg-slate-50"
            >
              Book a demo
            </Link>
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Free for 10 meetings/month · No credit card · Self-host the bot
          </p>
        </div>

        {/* Product preview — minimal mock, no external assets */}
        <div className="relative mx-auto mt-16 max-w-5xl">
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/[0.08]">
            {/* window chrome */}
            <div className="flex items-center gap-1.5 border-b border-slate-200 bg-slate-50 px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
              <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
              <span className="h-2.5 w-2.5 rounded-full bg-slate-300" />
              <span className="ml-3 text-xs text-slate-400">
                vaktram.com / meetings / Q4 planning sync
              </span>
            </div>
            <div className="grid gap-0 md:grid-cols-[1.1fr_1fr]">
              {/* Transcript pane */}
              <div className="border-b border-slate-100 p-6 md:border-b-0 md:border-r">
                <p className="eyebrow">Transcript</p>
                <div className="mt-4 space-y-3 text-[13.5px] text-slate-700">
                  <TranscriptLine
                    speaker="Priya"
                    text="Quick recap — we're on track to ship the BYOM gate by Friday."
                  />
                  <TranscriptLine
                    speaker="Arjun"
                    text="Backend's done. Frontend banner ships with the next deploy."
                  />
                  <TranscriptLine
                    speaker="Priya"
                    text="Let's add a heads-up on the verify-email page too."
                  />
                  <TranscriptLine
                    speaker="Arjun"
                    text="Already in the email template. Will mirror it to the page."
                  />
                </div>
              </div>
              {/* Summary pane */}
              <div className="p-6">
                <p className="eyebrow">Summary by Gemini 2.0 Flash</p>
                <h3 className="mt-3 text-[15px] font-semibold text-slate-900">
                  Q4 Planning Sync · 12 min
                </h3>
                <ul className="mt-4 space-y-2 text-[13.5px] text-slate-700">
                  <SummaryItem text="BYOM gate ships Friday — backend complete." />
                  <SummaryItem text="Frontend banner deploys next." />
                  <SummaryItem text="Heads-up to be mirrored on /verify-email." />
                </ul>
                <div className="mt-5 flex flex-wrap gap-1.5">
                  <Tag>action</Tag>
                  <Tag>byom</Tag>
                  <Tag>q4-planning</Tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TranscriptLine({ speaker, text }: { speaker: string; text: string }) {
  return (
    <p>
      <span className="font-semibold text-slate-900">{speaker}</span>
      <span className="ml-2 text-slate-500">{text}</span>
    </p>
  );
}

function SummaryItem({ text }: { text: string }) {
  return (
    <li className="flex items-start gap-2">
      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none text-teal-600" />
      <span>{text}</span>
    </li>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
      #{children}
    </span>
  );
}

// ── Logo strip ──────────────────────────────────────────────────────────
const LOGOS = [
  "Builders India",
  "Lakshya AI",
  "Northpath",
  "Kavach Labs",
  "Devloop",
  "Polaris",
  "Sankhya",
  "Anvayam",
];

function LogoStrip() {
  return (
    <section className="border-y border-slate-100 bg-slate-50/40 py-12">
      <div className="container-wide">
        <p className="text-center text-[13px] font-medium text-slate-500">
          Trusted by teams shipping with their own models
        </p>
        <div className="mt-6 grid grid-cols-2 items-center gap-x-6 gap-y-5 sm:grid-cols-4 lg:grid-cols-8">
          {LOGOS.map((name) => (
            <div
              key={name}
              className="text-center text-[15px] font-semibold tracking-tight text-slate-400"
            >
              {name}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Three pillars ───────────────────────────────────────────────────────
function Pillars() {
  return (
    <section className="py-24">
      <div className="container-wide">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">Built differently</p>
          <h2 className="display mt-3 text-3xl sm:text-5xl">
            A meeting platform that works for you,
            <br className="hidden sm:block" /> not your AI vendor.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-slate-600">
            Vaktram doesn't bundle a model. Plug in the LLM you already pay for
            and we handle the rest — joining, recording, transcription, search,
            and summaries.
          </p>
        </div>

        <div className="mt-16 grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 md:grid-cols-3">
          <Pillar
            icon={<Brain className="h-5 w-5" />}
            title="Bring your own model"
            body="Connect a key for Gemini, OpenAI, Anthropic, Mistral, Azure, or anything LiteLLM supports. Switch any time. Per-org rate limits and spend caps are yours to set."
          />
          <Pillar
            icon={<Calendar className="h-5 w-5" />}
            title="Joins every meeting"
            body="Connect Google Calendar and Vaktram dispatches a Playwright bot to every Meet, Zoom, or Teams link. The bot identifies itself and posts a recording-consent notice in chat."
          />
          <Pillar
            icon={<Search className="h-5 w-5" />}
            title="Searchable knowledge"
            body="Hybrid search across transcripts and summaries: Postgres FTS + pgvector embeddings combined with reciprocal rank fusion. Find a decision from three weeks ago in two keystrokes."
          />
        </div>
      </div>
    </section>
  );
}

function Pillar({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="bg-white p-8 transition-colors hover:bg-slate-50/50">
      <span className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-teal-700">
        {icon}
      </span>
      <h3 className="mt-5 text-lg font-semibold tracking-tight text-slate-900">
        {title}
      </h3>
      <p className="mt-2 text-[14.5px] leading-relaxed text-slate-600">
        {body}
      </p>
    </div>
  );
}

// ── Feature grid ────────────────────────────────────────────────────────
const FEATURES: { icon: React.ReactNode; title: string; body: string }[] = [
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Action items, not summaries",
    body: "Decisions, action items, and follow-ups extracted as structured data — pushed to your tools or queryable via API.",
  },
  {
    icon: <Users className="h-5 w-5" />,
    title: "Speaker-aware",
    body: "pyannote diarization stitches turns onto a single timeline so you know who said what, even on noisy calls.",
  },
  {
    icon: <Lock className="h-5 w-5" />,
    title: "Region-pinned data",
    body: "Audio and transcripts stay in the region you choose. Singapore, EU, US — your call, encrypted at rest with Fernet.",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "Ask your meetings",
    body: "Natural-language Q&A across every recording you've taken. Answers cite the exact transcript line they came from.",
  },
  {
    icon: <Calendar className="h-5 w-5" />,
    title: "Calendar-driven",
    body: "Sync once, then forget about us. Vaktram dispatches the bot at deploy time, leaves on its own when the meeting ends.",
  },
  {
    icon: <Brain className="h-5 w-5" />,
    title: "Self-hosted bot",
    body: "Run the Playwright bot on your VPS. No third-party recorder ever sees your meeting audio.",
  },
];

function FeatureGrid() {
  return (
    <section className="bg-slate-50 py-24">
      <div className="container-wide">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">Everything you need</p>
          <h2 className="display mt-3 text-3xl sm:text-5xl">
            One platform, every meeting surface.
          </h2>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-slate-200 bg-white p-6 transition-shadow hover:shadow-md hover:shadow-slate-900/[0.04]"
            >
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-slate-950 text-white">
                {f.icon}
              </span>
              <h3 className="mt-5 text-base font-semibold tracking-tight text-slate-900">
                {f.title}
              </h3>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-600">
                {f.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Pipeline visualisation ──────────────────────────────────────────────
function Pipeline() {
  const STEPS = [
    { num: "01", title: "Calendar sync", body: "We watch your connected calendars in your time zone." },
    { num: "02", title: "Bot joins", body: "A self-hosted Playwright bot joins as a guest with consent posted to chat." },
    { num: "03", title: "Audio captured", body: "PulseAudio routes the call into FLAC, encrypted in transit + at rest." },
    { num: "04", title: "Transcribe", body: "Groq Whisper runs the audio. pyannote stitches speaker turns." },
    { num: "05", title: "Your model writes", body: "Your LLM key drafts the summary, action items, and decisions." },
    { num: "06", title: "Searchable", body: "Hybrid (FTS + vector) search across every recording you've ever made." },
  ];

  return (
    <section className="py-24">
      <div className="container-wide">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">How it works</p>
          <h2 className="display mt-3 text-3xl sm:text-5xl">
            Six steps. None of them yours.
          </h2>
          <p className="mt-5 text-base leading-relaxed text-slate-600">
            From calendar invite to searchable knowledge, end to end.
          </p>
        </div>

        <ol className="mt-16 grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map((s) => (
            <li key={s.num} className="bg-white p-7">
              <span className="text-[12px] font-mono font-semibold tracking-wider text-teal-700">
                {s.num}
              </span>
              <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-900">
                {s.title}
              </h3>
              <p className="mt-1.5 text-[14px] leading-relaxed text-slate-600">
                {s.body}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

// ── Security band ───────────────────────────────────────────────────────
function SecurityBand() {
  return (
    <section className="border-y border-slate-100 bg-slate-50/40 py-20">
      <div className="container-wide">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.2fr] lg:items-center">
          <div>
            <p className="eyebrow">Built for trust</p>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              Your audio never leaves a perimeter you control.
            </h2>
            <p className="mt-5 text-base leading-relaxed text-slate-600">
              The bot runs on your infrastructure. Storage is region-pinned.
              LLM keys live encrypted with Fernet, decrypted only inside a
              memory boundary you can audit. We can't read your meetings — by
              design.
            </p>
            <Link
              href="/security"
              className="mt-6 inline-flex items-center gap-1.5 text-[14px] font-semibold text-slate-950 hover:underline"
            >
              Read the security overview
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            <SecurityRow title="Region-pinned storage" body="Singapore, EU, US." />
            <SecurityRow title="Fernet-encrypted keys" body="Decrypted in-memory only." />
            <SecurityRow title="Self-hosted bot" body="No third-party recorder." />
            <SecurityRow title="Recording consent" body="Posted to chat on join." />
            <SecurityRow title="HttpOnly auth" body="Refresh tokens never touch JS." />
            <SecurityRow title="Bot-secret signed" body="Internal callbacks authenticated." />
          </ul>
        </div>
      </div>
    </section>
  );
}

function SecurityRow({ title, body }: { title: string; body: string }) {
  return (
    <li className="flex items-start gap-3 rounded-md border border-slate-200 bg-white p-4">
      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none text-teal-600" />
      <div>
        <p className="text-[13.5px] font-semibold text-slate-900">{title}</p>
        <p className="text-[12.5px] text-slate-600">{body}</p>
      </div>
    </li>
  );
}

// ── CTA band ────────────────────────────────────────────────────────────
function CTABand() {
  return (
    <section className="bg-slate-950 py-20 text-white">
      <div className="container-wide">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="display text-3xl text-white sm:text-5xl">
            Ship your first meeting in under five minutes.
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-slate-300">
            Start free. No card. Bring your own LLM key and you're already
            ahead of every other notetaker on the market.
          </p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex items-center gap-1.5 rounded-md bg-white px-5 py-3 text-[15px] font-semibold text-slate-950 shadow-sm transition-colors hover:bg-slate-100"
            >
              Start free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md border border-white/20 px-5 py-3 text-[15px] font-semibold text-white transition-colors hover:bg-white/5"
            >
              Talk to us
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
