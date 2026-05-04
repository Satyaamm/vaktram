import Link from "next/link";
import { Check, Minus } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Free for 10 meetings/month. Pro at $12/seat. Team for unlimited meetings + advanced search. Bring your own LLM, pay only for the model you use.",
};


interface Tier {
  name: string;
  price: string;
  cadence: string;
  blurb: string;
  cta: { label: string; href: string };
  features: string[];
  highlight?: boolean;
}

const TIERS: Tier[] = [
  {
    name: "Free",
    price: "$0",
    cadence: "forever",
    blurb: "For early teams kicking the tyres.",
    cta: { label: "Start free", href: "/signup" },
    features: [
      "10 meetings per month",
      "Bring your own LLM key",
      "Google Meet, Zoom, Teams, Zoho",
      "Searchable transcripts + summaries",
      "Self-host the bot (1 instance)",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$12",
    cadence: "per seat / month",
    blurb: "For everyday work that needs to be findable later.",
    cta: { label: "Start trial", href: "/signup?plan=pro" },
    features: [
      "Unlimited meetings",
      "Bring your own LLM key",
      "Hybrid search (FTS + vectors)",
      "Speaker diarization",
      "Action items + decisions API",
      "Calendar auto-dispatch",
      "Email support",
    ],
    highlight: true,
  },
  {
    name: "Team",
    price: "$28",
    cadence: "per seat / month",
    blurb: "For organisations with shared knowledge surfaces.",
    cta: { label: "Talk to sales", href: "/contact" },
    features: [
      "Everything in Pro",
      "Org-wide search across members",
      "SAML SSO + SCIM provisioning",
      "Region-pinned storage",
      "Audit log + retention policies",
      "Dedicated bot pool",
      "Slack support",
    ],
  },
];

export default function PricingPage() {
  return (
    <main>
      <Hero />
      <Tiers />
      <ComparisonTable />
      <FAQ />
    </main>
  );
}

function Hero() {
  return (
    <section className="relative isolate overflow-hidden border-b border-slate-100 pb-20 pt-24">
      <div className="pointer-events-none absolute inset-0 bg-dot-grid opacity-60" />
      <div className="container-wide relative">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">Pricing</p>
          <h1 className="display mt-4 text-4xl sm:text-6xl">
            Pay for the platform.
            <br />
            Pay your model directly.
          </h1>
          <p className="mt-5 text-base leading-relaxed text-slate-600">
            We don't take a margin on inference. You bring your own LLM key;
            we charge a flat seat price for the platform — recording,
            transcription, search, and the dashboard.
          </p>
        </div>
      </div>
    </section>
  );
}

function Tiers() {
  return (
    <section className="py-20">
      <div className="container-wide">
        <div className="grid gap-6 lg:grid-cols-3">
          {TIERS.map((tier) => (
            <article
              key={tier.name}
              className={
                tier.highlight
                  ? "relative rounded-xl border-2 border-slate-950 bg-white p-8 shadow-xl shadow-slate-900/[0.06]"
                  : "rounded-xl border border-slate-200 bg-white p-8"
              }
            >
              {tier.highlight && (
                <span className="absolute -top-3 left-8 rounded-full bg-slate-950 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-white">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-semibold tracking-tight text-slate-900">
                {tier.name}
              </h3>
              <p className="mt-1 text-sm text-slate-600">{tier.blurb}</p>

              <div className="mt-6 flex items-baseline gap-1.5">
                <span className="display text-5xl">{tier.price}</span>
                <span className="text-sm text-slate-500">{tier.cadence}</span>
              </div>

              <Link
                href={tier.cta.href}
                className={
                  tier.highlight
                    ? "mt-6 inline-flex h-11 w-full items-center justify-center rounded-md bg-slate-950 text-[14.5px] font-semibold text-white transition-colors hover:bg-slate-800"
                    : "mt-6 inline-flex h-11 w-full items-center justify-center rounded-md border border-slate-200 bg-white text-[14.5px] font-semibold text-slate-900 transition-colors hover:bg-slate-50"
                }
              >
                {tier.cta.label}
              </Link>

              <ul className="mt-8 space-y-3">
                {tier.features.map((f) => (
                  <li
                    key={f}
                    className="flex items-start gap-2.5 text-[14px] text-slate-700"
                  >
                    <Check className="mt-0.5 h-4 w-4 flex-none text-teal-600" />
                    {f}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-slate-500">
          All plans include unlimited storage for transcripts. LLM token costs
          are billed by your provider, not by us.
        </p>
      </div>
    </section>
  );
}

const COMPARE_ROWS: { feature: string; free: string | true; pro: string | true; team: string | true }[] = [
  { feature: "Meetings per month", free: "10", pro: "Unlimited", team: "Unlimited" },
  { feature: "BYOM (your LLM key)", free: true, pro: true, team: true },
  { feature: "Auto-dispatch from calendar", free: false as unknown as string, pro: true, team: true },
  { feature: "Hybrid search (FTS + vectors)", free: false as unknown as string, pro: true, team: true },
  { feature: "Speaker diarization", free: false as unknown as string, pro: true, team: true },
  { feature: "SAML SSO / SCIM", free: false as unknown as string, pro: false as unknown as string, team: true },
  { feature: "Region-pinned storage", free: false as unknown as string, pro: false as unknown as string, team: true },
  { feature: "Audit log + retention policies", free: false as unknown as string, pro: false as unknown as string, team: true },
  { feature: "Support", free: "Community", pro: "Email", team: "Slack" },
];

function ComparisonTable() {
  return (
    <section className="border-t border-slate-100 bg-slate-50/40 py-20">
      <div className="container-wide">
        <h2 className="display text-center text-3xl sm:text-4xl">
          Compare plans
        </h2>
        <div className="mt-10 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-6 py-4 text-[12px] font-semibold uppercase tracking-wider text-slate-500">
                  Feature
                </th>
                <th className="px-6 py-4 text-[12px] font-semibold uppercase tracking-wider text-slate-500">
                  Free
                </th>
                <th className="px-6 py-4 text-[12px] font-semibold uppercase tracking-wider text-slate-500">
                  Pro
                </th>
                <th className="px-6 py-4 text-[12px] font-semibold uppercase tracking-wider text-slate-500">
                  Team
                </th>
              </tr>
            </thead>
            <tbody>
              {COMPARE_ROWS.map((row) => (
                <tr key={row.feature} className="border-b border-slate-100 last:border-0">
                  <td className="px-6 py-4 text-[14px] font-medium text-slate-900">
                    {row.feature}
                  </td>
                  <Cell value={row.free} />
                  <Cell value={row.pro} />
                  <Cell value={row.team} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Cell({ value }: { value: string | true | false }) {
  if (value === true) {
    return (
      <td className="px-6 py-4">
        <Check className="h-4 w-4 text-teal-600" />
      </td>
    );
  }
  if (value === false || value === ("false" as unknown)) {
    return (
      <td className="px-6 py-4">
        <Minus className="h-4 w-4 text-slate-300" />
      </td>
    );
  }
  return (
    <td className="px-6 py-4 text-[14px] text-slate-700">{String(value)}</td>
  );
}

const FAQS: { q: string; a: string }[] = [
  {
    q: "Do I need to bring my own LLM key?",
    a: "Yes. Vaktram is BYOM — bring your own model. We don't bundle inference, so you pay your provider directly and never get marked up by us. Gemini's free tier is enough to evaluate.",
  },
  {
    q: "What about transcription? Is that BYOM too?",
    a: "Transcription is platform-managed via Groq Whisper (free tier). You don't need to set anything up. If you need a different transcription model on Team, talk to us.",
  },
  {
    q: "Can I self-host the bot?",
    a: "Yes — every plan can run the Playwright bot on your VPS. Free is capped to one bot instance; Pro and Team scale horizontally.",
  },
  {
    q: "What happens to my recordings if I cancel?",
    a: "We export all your transcripts and summaries on request. Audio is deleted within 30 days of cancellation. The full data export is one API call away on Team plans.",
  },
];

function FAQ() {
  return (
    <section className="py-24">
      <div className="container-tight">
        <div className="text-center">
          <p className="eyebrow">FAQ</p>
          <h2 className="display mt-3 text-3xl sm:text-4xl">
            Common questions
          </h2>
        </div>
        <dl className="mx-auto mt-12 max-w-3xl divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
          {FAQS.map((f) => (
            <div key={f.q} className="px-6 py-6">
              <dt className="text-base font-semibold tracking-tight text-slate-900">
                {f.q}
              </dt>
              <dd className="mt-2 text-[14.5px] leading-relaxed text-slate-600">
                {f.a}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
