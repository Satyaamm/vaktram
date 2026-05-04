import Link from "next/link";
import {
  ArrowRight,
  Brain,
  Calendar,
  CheckCircle2,
  Database,
  FileSearch,
  Lock,
  MessageSquare,
  Mic,
  Users,
  Webhook,
} from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product",
  description:
    "How Vaktram works: BYOM-first meeting recording, transcription, search, and summaries — across Google Meet, Zoom, Teams, and Zoho.",
};

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://app.vaktram.com";

export default function ProductPage() {
  return (
    <main>
      <Hero />
      <Capability
        kicker="Capture"
        title="Joins every meeting on every platform that matters."
        body="A self-hosted Playwright bot dials into Google Meet, Zoom, Microsoft Teams, and Zoho Meeting as a guest. PulseAudio captures system audio into FLAC and uploads to your storage of choice."
        bullets={[
          "Auto-dispatch from your connected Google Calendar",
          "Recording-consent message posted to chat on join",
          "Region-pinned storage in Singapore, EU, or US",
          "Resilient against UI redesigns — selectors are versioned and probed weekly",
        ]}
        icon={<Mic className="h-5 w-5" />}
      />
      <Capability
        kicker="Transcribe"
        title="Speaker-aware transcripts in minutes."
        body="Groq Whisper converts the audio. pyannote diarization stitches speaker turns onto a single timeline. Punctuation, casing, and segment boundaries are preserved."
        bullets={[
          "Free Groq Whisper tier: 10 hours/day per workspace",
          "pyannote 3.1 speaker diarization (Docker service)",
          "Per-segment timestamps + confidence scores",
          "Works on calls up to 3 hours by default",
        ]}
        icon={<MessageSquare className="h-5 w-5" />}
        flip
      />
      <Capability
        kicker="Summarise"
        title="Your model writes the summary, not ours."
        body="Vaktram is BYOM. Plug in a key for any LiteLLM-compatible provider — Gemini, OpenAI, Claude, Mistral, Cohere, Azure — and your prompts run against the model your team already trusts."
        bullets={[
          "Decisions, action items, and follow-ups extracted as structured JSON",
          "Encrypted-at-rest API keys (Fernet, decrypted only in memory)",
          "Per-user provider/model overrides",
          "No platform markup on inference",
        ]}
        icon={<Brain className="h-5 w-5" />}
      />
      <Capability
        kicker="Search"
        title="Find the exact line, not the meeting it lived in."
        body="Hybrid search across every transcript and summary you've ever taken. Postgres full-text search and pgvector embeddings combined via reciprocal rank fusion."
        bullets={[
          "FTS + dense retrieval, fused per query",
          "Citations link directly back to the transcript timestamp",
          "Org-wide search across team members on Team plan",
          "Saved queries and alerts for tracking topics over time",
        ]}
        icon={<FileSearch className="h-5 w-5" />}
        flip
      />
      <FeatureMatrix />
      <CTA />
    </main>
  );
}

function Hero() {
  return (
    <section className="relative isolate overflow-hidden border-b border-slate-100 pb-20 pt-24">
      <div className="pointer-events-none absolute inset-0 bg-dot-grid opacity-60" />
      <div className="container-wide relative">
        <div className="mx-auto max-w-3xl text-center">
          <p className="eyebrow">Product</p>
          <h1 className="display mt-4 text-4xl sm:text-6xl">
            Capture, transcribe, summarise.
            <br />
            On the model you choose.
          </h1>
          <p className="mt-5 text-base leading-relaxed text-slate-600">
            Four capabilities, one platform. Each one designed so you keep
            control over your data, your model, and your spend.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href={`${APP_URL}/signup`}
              className="inline-flex items-center gap-1.5 rounded-md bg-slate-950 px-5 py-3 text-[15px] font-semibold text-white shadow-sm transition-all hover:bg-slate-800"
            >
              Start free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

function Capability({
  kicker,
  title,
  body,
  bullets,
  icon,
  flip,
}: {
  kicker: string;
  title: string;
  body: string;
  bullets: string[];
  icon: React.ReactNode;
  flip?: boolean;
}) {
  return (
    <section className="border-b border-slate-100 py-20">
      <div className="container-wide">
        <div
          className={
            flip
              ? "grid gap-12 lg:grid-cols-2 lg:items-center"
              : "grid gap-12 lg:grid-cols-2 lg:items-center"
          }
        >
          <div className={flip ? "order-2 lg:order-1" : ""}>
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-teal-700">
              {icon}
            </span>
            <p className="eyebrow mt-5">{kicker}</p>
            <h2 className="display mt-3 text-3xl sm:text-4xl">{title}</h2>
            <p className="mt-5 text-base leading-relaxed text-slate-600">
              {body}
            </p>
            <ul className="mt-6 space-y-2.5">
              {bullets.map((b) => (
                <li
                  key={b}
                  className="flex items-start gap-2.5 text-[14.5px] text-slate-700"
                >
                  <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none text-teal-600" />
                  {b}
                </li>
              ))}
            </ul>
          </div>

          <div className={flip ? "order-1 lg:order-2" : ""}>
            <CapabilityVisual kicker={kicker} />
          </div>
        </div>
      </div>
    </section>
  );
}

function CapabilityVisual({ kicker }: { kicker: string }) {
  // Lightweight, code-only visualisations per capability so the page reads
  // as a product page even without illustrations or screenshots.
  if (kicker === "Capture") {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-6">
        <p className="eyebrow">Live bot dispatch</p>
        <ul className="mt-4 space-y-2.5 text-[13.5px]">
          {[
            ["10:59:54", "Calendar event detected — Q4 Planning Sync"],
            ["10:59:56", "Bot dispatched to vps://212.38.94.234:8001"],
            ["11:00:01", "Joined Google Meet as 'Vaktram Notetaker'"],
            ["11:00:04", "Consent posted to chat"],
            ["11:00:05", "Recording started · vaktram_sink"],
          ].map(([t, msg]) => (
            <li key={t} className="flex gap-3">
              <span className="font-mono text-[12px] text-slate-500">{t}</span>
              <span className="text-slate-700">{msg}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  }
  if (kicker === "Transcribe") {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <p className="eyebrow">Diarized transcript</p>
        <div className="mt-4 space-y-3 text-[13.5px]">
          {[
            { who: "Priya", t: "00:08", line: "We need to ship the BYOM gate by Friday." },
            { who: "Arjun", t: "00:14", line: "Backend's done. Frontend banner deploys next." },
            { who: "Priya", t: "00:21", line: "Mirror the heads-up on /verify-email too." },
          ].map((s) => (
            <div key={s.t} className="grid grid-cols-[auto_1fr] gap-3">
              <span className="font-mono text-[12px] text-slate-400">{s.t}</span>
              <p>
                <span className="font-semibold text-slate-900">{s.who}</span>
                <span className="ml-2 text-slate-700">{s.line}</span>
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  }
  if (kicker === "Summarise") {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-950 p-6 text-slate-100">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-teal-300">
          Your config
        </p>
        <pre className="mt-3 overflow-x-auto text-[12.5px] leading-relaxed">
          <code>{`{
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "api_key": "sk-ant-•••••" ,
  "prompts": { "summary": "default" }
}`}</code>
        </pre>
      </div>
    );
  }
  // Search
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-[13.5px] text-slate-500">
        <FileSearch className="h-4 w-4 text-slate-400" />
        <span>“decision on byom gate launch”</span>
      </div>
      <ul className="mt-4 space-y-3 text-[13.5px]">
        <li className="rounded-md border border-slate-200 p-3">
          <p className="text-slate-900">
            <span className="font-semibold">Q4 Planning Sync</span>
            <span className="ml-2 text-[12px] text-slate-500">12 days ago · 00:08</span>
          </p>
          <p className="mt-1 text-slate-600">
            “…ship the BYOM gate by Friday — backend complete.”
          </p>
        </li>
      </ul>
    </div>
  );
}

const MATRIX: { icon: React.ReactNode; title: string; body: string }[] = [
  {
    icon: <Calendar className="h-5 w-5" />,
    title: "Calendar dispatch",
    body: "Connect Google Calendar once. Vaktram dispatches the bot at deploy time and leaves on its own.",
  },
  {
    icon: <Users className="h-5 w-5" />,
    title: "Speaker diarization",
    body: "pyannote 3.1 splits speakers; transcripts know who said what.",
  },
  {
    icon: <Webhook className="h-5 w-5" />,
    title: "Webhooks + API",
    body: "Get notified on transcript-ready and summary-ready, push action items to your tools.",
  },
  {
    icon: <Database className="h-5 w-5" />,
    title: "BYOK storage",
    body: "Pin storage to your Supabase, R2, or S3. We never see your audio.",
  },
  {
    icon: <Lock className="h-5 w-5" />,
    title: "Encrypted at rest",
    body: "Fernet encryption for every API key. Decrypted only in memory.",
  },
  {
    icon: <Brain className="h-5 w-5" />,
    title: "Any LiteLLM provider",
    body: "Gemini, OpenAI, Anthropic, Mistral, Azure, Cohere, Vertex — switch any time.",
  },
];

function FeatureMatrix() {
  return (
    <section className="bg-slate-50 py-20">
      <div className="container-wide">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">Built-in</p>
          <h2 className="display mt-3 text-3xl sm:text-4xl">
            Everything else you'd build yourself.
          </h2>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {MATRIX.map((m) => (
            <div
              key={m.title}
              className="rounded-xl border border-slate-200 bg-white p-6"
            >
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-slate-950 text-white">
                {m.icon}
              </span>
              <h3 className="mt-5 text-base font-semibold tracking-tight text-slate-900">
                {m.title}
              </h3>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-600">
                {m.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="bg-slate-950 py-20 text-white">
      <div className="container-wide text-center">
        <h2 className="display text-3xl text-white sm:text-4xl">
          Ready to plug in your model?
        </h2>
        <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href={`${APP_URL}/signup`}
            className="inline-flex items-center gap-1.5 rounded-md bg-white px-5 py-3 text-[15px] font-semibold text-slate-950 transition-colors hover:bg-slate-100"
          >
            Start free
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/pricing"
            className="inline-flex items-center rounded-md border border-white/20 px-5 py-3 text-[15px] font-semibold text-white transition-colors hover:bg-white/5"
          >
            See pricing
          </Link>
        </div>
      </div>
    </section>
  );
}
