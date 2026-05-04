import Link from "next/link";
import { ArrowRight, Quote } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Customers",
  description:
    "Why teams shipping with their own models choose Vaktram for meeting notes, transcripts, and searchable knowledge.",
};


interface Story {
  company: string;
  role: string;
  name: string;
  quote: string;
  metrics: { value: string; label: string }[];
}

// Placeholder story content — replace with real customer copy as it lands.
const STORIES: Story[] = [
  {
    company: "Builders India",
    role: "Head of Engineering",
    name: "Aanya Mehta",
    quote:
      "Every other notetaker forced us onto their LLM. Vaktram lets us point at our own Gemini key and walk away. Two days from signup to first transcript hitting our knowledge base.",
    metrics: [
      { value: "92%", label: "of meetings auto-captured" },
      { value: "0", label: "vendor LLM costs" },
      { value: "8 min", label: "to bot dispatch" },
    ],
  },
  {
    company: "Lakshya AI",
    role: "Co-founder",
    name: "Rohan Iyer",
    quote:
      "We vetted four meeting platforms before Vaktram. The bot self-hosting + region-pinned storage was the dealbreaker — nothing else came close on data residency.",
    metrics: [
      { value: "100%", label: "data in ap-south-1" },
      { value: "3 min", label: "weekly setup" },
    ],
  },
  {
    company: "Kavach Labs",
    role: "VP Operations",
    name: "Priya Narayan",
    quote:
      "Searchable transcripts changed how we run product reviews. We don't argue about what was decided three weeks ago anymore — we cite the line.",
    metrics: [
      { value: "5x", label: "faster recall" },
      { value: "1.4k", label: "queries/month" },
    ],
  },
];

export default function CustomersPage() {
  return (
    <main>
      <Hero />
      <Stories />
      <CTA />
    </main>
  );
}

function Hero() {
  return (
    <section className="border-b border-slate-100 py-24">
      <div className="container-wide text-center">
        <p className="eyebrow">Customers</p>
        <h1 className="display mx-auto mt-4 max-w-3xl text-balance text-4xl sm:text-6xl">
          Teams that own their model own their meetings.
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-slate-600">
          From AI-native startups to enterprise security teams — here's why
          they picked Vaktram over the bundled-LLM alternatives.
        </p>
      </div>
    </section>
  );
}

function Stories() {
  return (
    <section className="py-20">
      <div className="container-wide grid gap-10">
        {STORIES.map((s, i) => (
          <article
            key={s.company}
            className={
              i % 2 === 0
                ? "grid gap-8 rounded-2xl border border-slate-200 bg-white p-8 lg:grid-cols-[1.4fr_1fr] lg:p-12"
                : "grid gap-8 rounded-2xl border border-slate-200 bg-slate-50 p-8 lg:grid-cols-[1fr_1.4fr] lg:p-12"
            }
          >
            <div className={i % 2 === 0 ? "" : "lg:order-2"}>
              <Quote className="h-7 w-7 text-teal-600" />
              <p className="mt-4 text-balance text-xl leading-relaxed text-slate-900 sm:text-2xl">
                {s.quote}
              </p>
              <p className="mt-6 text-sm font-semibold text-slate-900">
                {s.name}
                <span className="ml-2 font-normal text-slate-500">
                  · {s.role}, {s.company}
                </span>
              </p>
            </div>
            <div className={i % 2 === 0 ? "" : "lg:order-1"}>
              <dl className="grid grid-cols-2 gap-6">
                {s.metrics.map((m) => (
                  <div key={m.label}>
                    <dt className="display text-3xl sm:text-4xl">{m.value}</dt>
                    <dd className="mt-1 text-[13px] text-slate-600">{m.label}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="bg-slate-950 py-20 text-white">
      <div className="container-wide text-center">
        <h2 className="display text-3xl text-white sm:text-4xl">
          Want to be next?
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-slate-300">
          Tell us about your meeting volume and your LLM stack. We'll get you
          shipping in under a day.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="/contact"
            className="inline-flex items-center gap-1.5 rounded-md bg-white px-5 py-3 text-[15px] font-semibold text-slate-950 transition-colors hover:bg-slate-100"
          >
            Talk to us
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center rounded-md border border-white/20 px-5 py-3 text-[15px] font-semibold text-white transition-colors hover:bg-white/5"
          >
            Or start free
          </Link>
        </div>
      </div>
    </section>
  );
}
