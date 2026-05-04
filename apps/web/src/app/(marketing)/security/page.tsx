import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Globe,
  KeyRound,
  Lock,
  Server,
  ShieldCheck,
  UserX,
} from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Security",
  description:
    "How Vaktram protects your meeting audio, transcripts, and LLM credentials. Encryption, region pinning, self-hosted bot, BYOM, and compliance posture.",
};

export default function SecurityPage() {
  return (
    <main>
      <Hero />
      <Pillars />
      <Practices />
      <Compliance />
      <CTA />
    </main>
  );
}

function Hero() {
  return (
    <section className="relative isolate overflow-hidden border-b border-slate-100 pt-24 pb-20">
      <div className="pointer-events-none absolute inset-0 bg-dot-grid opacity-60" />
      <div className="container-wide relative">
        <div className="mx-auto max-w-3xl text-center">
          <p className="eyebrow">Security</p>
          <h1 className="display mt-4 text-4xl sm:text-6xl">
            Your audio never leaves
            <br />
            a perimeter you control.
          </h1>
          <p className="mt-5 text-base leading-relaxed text-slate-600">
            We built Vaktram for teams that have to answer hard data
            questions: where does my data live, who has access, and what
            happens if I leave. Here are the answers, in plain English.
          </p>
        </div>
      </div>
    </section>
  );
}

const PILLARS: { icon: React.ReactNode; title: string; body: string }[] = [
  {
    icon: <Server className="h-5 w-5" />,
    title: "Self-hosted bot",
    body: "The Playwright bot runs on your VPS. Audio never touches a third-party recording service.",
  },
  {
    icon: <Globe className="h-5 w-5" />,
    title: "Region-pinned storage",
    body: "Pick Singapore, EU, or US. Transcripts and audio stay there. No cross-region replication without consent.",
  },
  {
    icon: <KeyRound className="h-5 w-5" />,
    title: "BYOM credentials",
    body: "Your LLM key, encrypted at rest with Fernet, decrypted only in memory at request time. No platform-side fan-out.",
  },
  {
    icon: <UserX className="h-5 w-5" />,
    title: "We can't read your meetings",
    body: "Inference runs against your provider. Your transcripts are stored in your row in our DB; no employee browses them.",
  },
];

function Pillars() {
  return (
    <section className="py-20">
      <div className="container-wide">
        <div className="grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-4">
          {PILLARS.map((p) => (
            <div key={p.title} className="bg-white p-7">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-slate-950 text-white">
                {p.icon}
              </span>
              <h3 className="mt-5 text-base font-semibold tracking-tight text-slate-900">
                {p.title}
              </h3>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-600">
                {p.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const PRACTICES: { area: string; bullets: string[] }[] = [
  {
    area: "Authentication",
    bullets: [
      "Custom JWT auth, HS256 pinned (no algorithm-confusion attacks)",
      "Refresh tokens HttpOnly + Secure, rotated on every refresh",
      "Redis revocation list — logout invalidates the refresh token",
      "Bcrypt cost 12, constant-time login (no email enumeration)",
      "Email-verification tokens single-use with constant-time compare",
    ],
  },
  {
    area: "Transport & storage",
    bullets: [
      "TLS-only ingress (HSTS preload header set)",
      "Audio FLAC encrypted in transit, written via service-role key",
      "User LLM keys encrypted with Fernet (AES-128-CBC + HMAC)",
      "PostgreSQL backups encrypted at rest by Supabase",
      "Configurable retention windows per organisation",
    ],
  },
  {
    area: "Internal services",
    bullets: [
      "Bot service requires X-Bot-Auth shared secret on every request",
      "QStash webhook signatures verified (HS256, current + next keys)",
      "Worker → API callbacks authenticated with the same secret",
      "Strict CSP + frame-ancestors none on every page",
      "Rate limit: 60 req/min/user, 3 verification emails/hour/email",
    ],
  },
  {
    area: "Operational",
    bullets: [
      "Daily retention purge (org-policy aware, GDPR Art. 5(1)(e))",
      "Audit log for org admin actions (compliance-exportable)",
      "Weekly bot-platform selector health probe",
      "Centralised structured logs (request-id correlation)",
      "Sentry for error tracking; OTel-ready trace export",
    ],
  },
];

function Practices() {
  return (
    <section className="border-t border-slate-100 bg-slate-50/40 py-20">
      <div className="container-wide">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">Controls</p>
          <h2 className="display mt-3 text-3xl sm:text-4xl">
            Every layer hardened.
          </h2>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          {PRACTICES.map((p) => (
            <div
              key={p.area}
              className="rounded-xl border border-slate-200 bg-white p-7"
            >
              <h3 className="text-base font-semibold tracking-tight text-slate-900">
                {p.area}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {p.bullets.map((b) => (
                  <li
                    key={b}
                    className="flex items-start gap-2.5 text-[14px] text-slate-700"
                  >
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none text-teal-600" />
                    {b}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Compliance() {
  return (
    <section className="py-20">
      <div className="container-wide">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.2fr] lg:items-start">
          <div>
            <p className="eyebrow">Compliance</p>
            <h2 className="display mt-3 text-3xl sm:text-4xl">
              Where we are today.
            </h2>
            <p className="mt-5 text-base leading-relaxed text-slate-600">
              We're a young company and we're honest about that. Here's our
              current posture and what we're working toward.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Status
              title="GDPR-ready"
              status="now"
              body="Region pinning, retention policies, data export endpoint, and a recording-consent disclosure on every join."
              icon={<ShieldCheck className="h-5 w-5" />}
            />
            <Status
              title="SOC 2 Type II"
              status="2026"
              body="Audit kicks off Q3 2026. Most controls are already implemented; we're collecting evidence."
              icon={<Lock className="h-5 w-5" />}
            />
            <Status
              title="DPA on request"
              status="now"
              body="Standard DPA + EU Standard Contractual Clauses available before any contract is signed."
              icon={<ShieldCheck className="h-5 w-5" />}
            />
            <Status
              title="ISO 27001"
              status="2026"
              body="Scoped for after the SOC 2 audit closes. Ask for our roadmap if you need more detail."
              icon={<Lock className="h-5 w-5" />}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function Status({
  title,
  status,
  body,
  icon,
}: {
  title: string;
  status: "now" | "2026";
  body: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-teal-700">
          {icon}
        </span>
        <span
          className={
            status === "now"
              ? "rounded-full bg-teal-50 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-teal-700"
              : "rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-amber-700"
          }
        >
          {status === "now" ? "Available" : "Targeting 2026"}
        </span>
      </div>
      <h3 className="mt-5 text-base font-semibold tracking-tight text-slate-900">
        {title}
      </h3>
      <p className="mt-1 text-[13.5px] leading-relaxed text-slate-600">
        {body}
      </p>
    </div>
  );
}

function CTA() {
  return (
    <section className="bg-slate-950 py-20 text-white">
      <div className="container-wide text-center">
        <h2 className="display text-3xl text-white sm:text-4xl">
          Have a security questionnaire?
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-slate-300">
          We'll fill it out the same week. Real answers, no marketing fluff.
        </p>
        <Link
          href="/contact"
          className="mt-8 inline-flex items-center gap-1.5 rounded-md bg-white px-5 py-3 text-[15px] font-semibold text-slate-950 transition-colors hover:bg-slate-100"
        >
          Send it over
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
