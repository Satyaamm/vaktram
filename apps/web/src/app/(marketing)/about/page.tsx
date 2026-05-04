import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About",
  description:
    "Vaktram is a meeting-notes platform built for teams that want to own their model and their data.",
};


export default function AboutPage() {
  return (
    <main>
      <section className="border-b border-slate-100 py-24">
        <div className="container-wide">
          <div className="mx-auto max-w-3xl text-center">
            <p className="eyebrow">About</p>
            <h1 className="display mt-4 text-4xl sm:text-6xl">
              We started Vaktram because every other notetaker
              <br />
              picked the model for you.
            </h1>
            <p className="mt-6 text-base leading-relaxed text-slate-600">
              The AI meeting space settled on a deal: vendor X bundles model
              Y, and you live with it. That's a fine deal until the team
              already has a Gemini contract, or has to keep data on Indian
              soil, or wants Claude on Tuesdays and Mistral on Thursdays.
            </p>
            <p className="mt-4 text-base leading-relaxed text-slate-600">
              Vaktram is a meeting platform first, an AI app second. We
              capture, transcribe, and search; you bring the model that
              writes. That separation is the whole product.
            </p>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container-wide">
          <div className="mx-auto max-w-3xl">
            <h2 className="display text-3xl sm:text-4xl">
              What we believe.
            </h2>
            <ul className="mt-10 space-y-7 text-base leading-relaxed text-slate-700">
              <Belief
                title="Your model is your model."
                body="We don't markup inference. We don't fan out your prompts to a third party. The provider you signed up with is the provider that runs your prompts."
              />
              <Belief
                title="Data residency is non-negotiable."
                body="Where your audio lives matters — to compliance, to customers, and to anyone who's ever filled in a security questionnaire. We pin to a region you choose, and we don't move it."
              />
              <Belief
                title="Build less, integrate more."
                body="There's already a great calendar, a great recorder, a great LLM, and a great vector database. Our job is to glue them together and stay out of your way."
              />
              <Belief
                title="Show, don't market."
                body="If we don't have SOC 2 yet, we say so. If a feature is half-built, we mark it as such. The product makes the case better than the homepage ever could."
              />
            </ul>
          </div>
        </div>
      </section>

      <section className="bg-slate-950 py-20 text-white">
        <div className="container-wide text-center">
          <h2 className="display text-3xl text-white sm:text-4xl">
            Want to build with us?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-slate-300">
            Hiring is selective and intentional — we'd rather meet you when
            we both have the right shape.
          </p>
          <Link
            href="mailto:hello@vaktram.com"
            className="mt-8 inline-flex items-center gap-1.5 rounded-md bg-white px-5 py-3 text-[15px] font-semibold text-slate-950 transition-colors hover:bg-slate-100"
          >
            Say hello
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </main>
  );
}

function Belief({ title, body }: { title: string; body: string }) {
  return (
    <li>
      <p className="text-lg font-semibold tracking-tight text-slate-900">
        {title}
      </p>
      <p className="mt-2 text-[15.5px] leading-relaxed text-slate-600">
        {body}
      </p>
    </li>
  );
}
