"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import {
  Mic,
  FileText,
  Cpu,
  Search,
  Calendar,
  Users,
  ArrowRight,
  Check,
  Sparkles,
  Video,
  Play,
  Shield,
  Zap,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PLAN_LIMITS } from "@/lib/constants";

/* ─── subtle fade that triggers on scroll ─── */
const reveal = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.6, ease: [0.25, 0.4, 0.25, 1] as const },
  }),
};

/* ─── data ─── */

const features = [
  {
    icon: Mic,
    title: "Smart Transcription",
    desc: "Speaker-labeled, real-time transcription across Zoom, Meet, and Teams. No more frantic note-taking.",
    color: "teal",
  },
  {
    icon: FileText,
    title: "AI Summaries",
    desc: "Summaries, decisions, and action items extracted automatically. Read a 60-min meeting in 2 minutes.",
    color: "amber",
  },
  {
    icon: Cpu,
    title: "Bring Your Own Model",
    desc: "GPT-4o, Claude, Gemini, Ollama — your keys, your rules. We never touch your data.",
    color: "teal",
  },
  {
    icon: Search,
    title: "Semantic Search",
    desc: 'Ask "what did Sarah say about the Q3 budget?" and get the exact moment. Across all meetings.',
    color: "amber",
  },
  {
    icon: Calendar,
    title: "Calendar Sync",
    desc: "Connect Google Calendar and the bot joins automatically. Zero effort, zero missed meetings.",
    color: "teal",
  },
  {
    icon: Users,
    title: "Team Workspace",
    desc: "Share notes, assign action items, track follow-ups. Everyone stays on the same page.",
    color: "amber",
  },
];

const steps = [
  {
    num: "01",
    icon: Calendar,
    title: "Connect your calendar",
    desc: "Link Google Calendar. Vaktram detects your upcoming meetings and gets ready.",
  },
  {
    num: "02",
    icon: Video,
    title: "Bot joins automatically",
    desc: "Our bot slips into the call, records audio, and transcribes every word with speaker labels.",
  },
  {
    num: "03",
    icon: Sparkles,
    title: "Get your summary",
    desc: "Within seconds of the call ending, you get a structured summary with action items and key decisions.",
  },
];

const providers = ["OpenAI", "Claude", "Gemini", "Groq", "Ollama", "Azure"];

const pricingTiers = [
  { key: "free" as const, cta: "Start for free", popular: false },
  { key: "pro" as const, cta: "Start free trial", popular: true },
  { key: "team" as const, cta: "Start free trial", popular: false },
];

/* ─── page ─── */

export default function LandingPage() {
  const [activeProvider, setActiveProvider] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 1], [1, 0.96]);

  useEffect(() => {
    const id = setInterval(() => setActiveProvider((p) => (p + 1) % providers.length), 2200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="scroll-smooth">
      {/* ════════════ HERO ════════════ */}
      <section ref={heroRef} className="relative overflow-hidden pt-16 pb-24 md:pt-28 md:pb-36">
        {/* Ambient blobs */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-40 -right-40 h-[500px] w-[500px] rounded-full bg-teal-200/40 blur-[100px]" />
          <div className="absolute top-1/2 -left-32 h-[400px] w-[400px] rounded-full bg-amber-200/30 blur-[100px]" />
          <div className="absolute bottom-0 right-1/3 h-[300px] w-[300px] rounded-full bg-teal-100/50 blur-[80px]" />
        </div>

        {/* Dot grid pattern */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: "radial-gradient(circle, #0F766E 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />

        <motion.div style={{ opacity: heroOpacity, scale: heroScale }} className="relative">
          <div className="container mx-auto px-4">
            <div className="mx-auto max-w-4xl text-center">
              {/* Pill badge */}
              <motion.div
                initial={{ opacity: 0, y: -12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <span className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-4 py-1.5 text-sm font-medium text-teal-800">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-teal-500" />
                  </span>
                  Now in Beta — Free to use
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1
                className="mt-8 text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl md:text-6xl lg:text-7xl"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15, duration: 0.7, ease: [0.25, 0.4, 0.25, 1] }}
              >
                Stop taking notes.
                <br />
                <span className="bg-gradient-to-r from-teal-700 via-teal-600 to-teal-500 bg-clip-text text-transparent">
                  Start making decisions.
                </span>
              </motion.h1>

              {/* Sub */}
              <motion.p
                className="mx-auto mt-6 max-w-2xl text-lg text-slate-500 md:text-xl leading-relaxed"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35, duration: 0.6 }}
              >
                Vaktram records, transcribes, and summarizes your meetings — using the AI model{" "}
                <em className="font-medium text-slate-700 not-italic">you</em> choose.
                Your keys. Your data. Your way.
              </motion.p>

              {/* CTAs */}
              <motion.div
                className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.5 }}
              >
                <Button
                  size="lg"
                  asChild
                  className="group bg-teal-700 hover:bg-teal-800 text-white px-8 h-13 text-base rounded-xl shadow-lg shadow-teal-700/25 transition-all duration-200 hover:shadow-xl hover:shadow-teal-700/30"
                >
                  <Link href="/signup">
                    Get started free
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  asChild
                  className="h-13 text-base rounded-xl px-8 border-slate-200 bg-white/80 backdrop-blur-sm text-slate-700 hover:bg-white hover:border-slate-300 transition-all duration-200"
                >
                  <Link href="#how-it-works">
                    <Play className="mr-2 h-4 w-4" />
                    See how it works
                  </Link>
                </Button>
              </motion.div>

              {/* Trust signals */}
              <motion.div
                className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-400"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7, duration: 0.5 }}
              >
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-teal-600" />
                  No credit card
                </span>
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-teal-600" />
                  10 free meetings/mo
                </span>
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5 text-teal-600" />
                  Works with any LLM
                </span>
              </motion.div>
            </div>

            {/* Floating product preview mockup */}
            <motion.div
              className="relative mx-auto mt-16 max-w-3xl"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.8, ease: [0.25, 0.4, 0.25, 1] }}
            >
              <div className="rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-sm p-6 shadow-2xl shadow-slate-900/[0.08]">
                {/* Fake browser bar */}
                <div className="flex items-center gap-2 mb-5">
                  <div className="flex gap-1.5">
                    <div className="h-3 w-3 rounded-full bg-slate-200" />
                    <div className="h-3 w-3 rounded-full bg-slate-200" />
                    <div className="h-3 w-3 rounded-full bg-slate-200" />
                  </div>
                  <div className="flex-1 mx-4 h-7 rounded-lg bg-slate-100 flex items-center px-3">
                    <span className="text-xs text-slate-400">app.vaktram.com/meetings/standup-mar-3</span>
                  </div>
                </div>
                {/* Fake content */}
                <div className="grid md:grid-cols-5 gap-4">
                  <div className="md:col-span-3 space-y-3">
                    <div className="h-5 w-48 rounded bg-slate-100" />
                    <div className="space-y-2">
                      <div className="h-3 w-full rounded bg-slate-50" />
                      <div className="h-3 w-5/6 rounded bg-slate-50" />
                      <div className="h-3 w-4/6 rounded bg-slate-50" />
                    </div>
                    <div className="mt-4 flex gap-2">
                      <div className="h-7 w-20 rounded-lg bg-teal-50 border border-teal-100" />
                      <div className="h-7 w-24 rounded-lg bg-amber-50 border border-amber-100" />
                    </div>
                  </div>
                  <div className="md:col-span-2 rounded-xl bg-gradient-to-br from-teal-50 to-teal-100/50 border border-teal-100 p-4">
                    <div className="h-4 w-24 rounded bg-teal-200/60 mb-3" />
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-teal-400" />
                        <div className="h-3 w-full rounded bg-teal-100" />
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-teal-400" />
                        <div className="h-3 w-5/6 rounded bg-teal-100" />
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-amber-400" />
                        <div className="h-3 w-4/6 rounded bg-teal-100" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Glow behind */}
              <div className="pointer-events-none absolute -inset-4 -z-10 rounded-3xl bg-gradient-to-b from-teal-100/60 to-transparent blur-2xl" />
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* ════════════ SOCIAL PROOF BAR ════════════ */}
      <section className="border-y border-slate-100 bg-slate-50/60 py-10">
        <div className="container mx-auto px-4">
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto text-center"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.5 }}
          >
            {[
              { value: "10K+", label: "Meetings recorded" },
              { value: "500+", label: "Teams using BYOM" },
              { value: "99.9%", label: "Transcription accuracy" },
              { value: "<30s", label: "Avg. summary time" },
            ].map((stat, i) => (
              <motion.div key={stat.label} variants={reveal} custom={i}>
                <p className="text-2xl md:text-3xl font-bold text-teal-700 tabular-nums">
                  {stat.value}
                </p>
                <p className="mt-1 text-sm text-slate-500">{stat.label}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ════════════ FEATURES ════════════ */}
      <section id="features" className="py-24 md:py-32 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            className="mx-auto max-w-2xl text-center mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.4 }}
            variants={reveal}
          >
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-700 mb-3">
              Features
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Everything your meetings need.
              <br />
              Nothing they don&apos;t.
            </h2>
            <p className="mt-4 text-lg text-slate-500 leading-relaxed">
              From live transcription to semantic search — we handle the busywork so you can focus on what matters.
            </p>
          </motion.div>

          <motion.div
            className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
          >
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                variants={reveal}
                custom={i}
                className="group relative rounded-2xl border border-slate-100 bg-white p-6 transition-all duration-300 hover:border-slate-200 hover:shadow-lg hover:shadow-slate-900/[0.04]"
              >
                <div
                  className={`mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl transition-colors duration-200 ${
                    f.color === "teal"
                      ? "bg-teal-50 group-hover:bg-teal-100 text-teal-700"
                      : "bg-amber-50 group-hover:bg-amber-100 text-amber-600"
                  }`}
                >
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-1.5">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ════════════ BYOM ════════════ */}
      <section id="byom" className="py-24 md:py-32 bg-gradient-to-b from-slate-50 to-white">
        <div className="container mx-auto px-4">
          <div className="grid gap-12 lg:grid-cols-2 items-center max-w-6xl mx-auto">
            {/* Text side */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={reveal}
            >
              <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-sm font-medium text-amber-700 mb-5">
                <Cpu className="h-3.5 w-3.5" />
                BYOM
              </div>
              <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
                Your model.{" "}
                <span className="text-teal-700">Your rules.</span>
              </h2>
              <p className="mt-4 text-lg text-slate-500 leading-relaxed">
                Most tools lock you into their AI provider. Vaktram lets you plug in
                any LLM — cloud or local. Switch anytime, keep everything.
              </p>
              <ul className="mt-8 space-y-3">
                {[
                  { icon: Shield, text: "Your API keys stay on your machine" },
                  { icon: Zap, text: "Switch providers without losing history" },
                  { icon: Globe, text: "Run offline with local models via Ollama" },
                ].map((item) => (
                  <li key={item.text} className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                      <item.icon className="h-4 w-4" />
                    </div>
                    <span className="text-slate-600">{item.text}</span>
                  </li>
                ))}
              </ul>
              <Button
                className="mt-8 bg-teal-700 hover:bg-teal-800 text-white rounded-xl px-6 h-11 shadow-lg shadow-teal-700/20 transition-all duration-200"
                asChild
              >
                <Link href="/signup">
                  Try it free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </motion.div>

            {/* Interactive provider card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.15 }}
            >
              <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-900/[0.06]">
                <div className="flex items-center justify-between mb-6">
                  <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                    Active Model
                  </p>
                  <span className="flex items-center gap-1.5 text-xs text-teal-700 font-medium">
                    <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
                    Connected
                  </span>
                </div>

                <div className="h-16 flex items-center justify-center">
                  <AnimatePresence mode="wait">
                    <motion.span
                      key={providers[activeProvider]}
                      initial={{ opacity: 0, y: 16, filter: "blur(4px)" }}
                      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                      exit={{ opacity: 0, y: -16, filter: "blur(4px)" }}
                      transition={{ duration: 0.35 }}
                      className="text-3xl font-bold text-slate-900"
                    >
                      {providers[activeProvider]}
                    </motion.span>
                  </AnimatePresence>
                </div>

                <div className="mt-6 grid grid-cols-3 gap-2">
                  {providers.map((p, i) => (
                    <button
                      key={p}
                      onClick={() => setActiveProvider(i)}
                      className={`rounded-lg border px-3 py-2 text-sm font-medium transition-all duration-200 cursor-pointer ${
                        i === activeProvider
                          ? "border-teal-600 bg-teal-50 text-teal-700 shadow-sm"
                          : "border-slate-150 text-slate-400 hover:border-slate-300 hover:text-slate-600"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>

                <div className="mt-6 rounded-lg bg-slate-50 border border-slate-100 p-3">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <code className="font-mono text-[11px] text-slate-400">
                      {">"} Using {providers[activeProvider].toLowerCase()} for summarization...
                    </code>
                    <span className="ml-auto inline-block h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse" />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════ HOW IT WORKS ════════════ */}
      <section id="how-it-works" className="py-24 md:py-32 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            className="mx-auto max-w-xl text-center mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.4 }}
            variants={reveal}
          >
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-700 mb-3">
              How it works
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Three steps. Zero effort.
            </h2>
          </motion.div>

          <div className="relative max-w-4xl mx-auto">
            {/* Connector line */}
            <div className="hidden md:block absolute top-[52px] left-[16%] right-[16%] h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />

            <motion.div
              className="grid gap-10 md:grid-cols-3"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
            >
              {steps.map((step, i) => (
                <motion.div
                  key={step.num}
                  variants={reveal}
                  custom={i}
                  className="relative text-center"
                >
                  {/* Icon */}
                  <div className="relative mx-auto mb-5 flex h-[72px] w-[72px] items-center justify-center">
                    <div className="absolute inset-0 rounded-2xl bg-teal-50 rotate-6 transition-transform duration-300 group-hover:rotate-12" />
                    <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-white border border-slate-200 shadow-sm">
                      <step.icon className="h-6 w-6 text-teal-700" />
                    </div>
                  </div>

                  {/* Step number */}
                  <span className="inline-block text-xs font-bold tracking-widest text-teal-600 mb-2">
                    STEP {step.num}
                  </span>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">{step.title}</h3>
                  <p className="text-sm text-slate-500 leading-relaxed max-w-[280px] mx-auto">
                    {step.desc}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════ PRICING ════════════ */}
      <section id="pricing" className="py-24 md:py-32 bg-slate-50/80">
        <div className="container mx-auto px-4">
          <motion.div
            className="mx-auto max-w-xl text-center mb-14"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.4 }}
            variants={reveal}
          >
            <p className="text-sm font-semibold uppercase tracking-widest text-teal-700 mb-3">
              Pricing
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Simple pricing. No surprises.
            </h2>
            <p className="mt-3 text-lg text-slate-500">
              Start free, upgrade when you&apos;re ready.
            </p>
          </motion.div>

          <motion.div
            className="grid gap-5 md:grid-cols-3 max-w-4xl mx-auto items-start"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
          >
            {pricingTiers.map((tier, i) => {
              const plan = PLAN_LIMITS[tier.key];
              return (
                <motion.div
                  key={tier.key}
                  variants={reveal}
                  custom={i}
                  className={`relative rounded-2xl border bg-white p-7 transition-all duration-300 hover:shadow-lg hover:shadow-slate-900/[0.04] ${
                    tier.popular
                      ? "border-teal-600 shadow-lg shadow-teal-700/[0.08] md:-mt-2 md:pb-9"
                      : "border-slate-200 shadow-sm"
                  }`}
                >
                  {tier.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="rounded-full bg-teal-700 px-3 py-1 text-xs font-semibold text-white shadow-sm">
                        Most popular
                      </span>
                    </div>
                  )}
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                    {plan.name}
                  </h3>
                  <div className="mt-3 mb-5">
                    <span className="text-4xl font-bold text-slate-900">
                      ${plan.price}
                    </span>
                    <span className="text-slate-400 text-sm">/mo</span>
                  </div>
                  <ul className="space-y-2.5 mb-7">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm">
                        <Check className="h-4 w-4 shrink-0 mt-0.5 text-teal-600" />
                        <span className="text-slate-600">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    asChild
                    className={`w-full rounded-xl h-10 text-sm font-medium transition-all duration-200 ${
                      tier.popular
                        ? "bg-teal-700 hover:bg-teal-800 text-white shadow-md shadow-teal-700/20"
                        : "bg-white border border-teal-700 text-teal-700 hover:bg-teal-50"
                    }`}
                    variant={tier.popular ? "default" : "outline"}
                  >
                    <Link href="/signup">{tier.cta}</Link>
                  </Button>
                </motion.div>
              );
            })}
          </motion.div>

          <motion.p
            className="text-center mt-8 text-sm text-slate-400"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
          >
            Need more?{" "}
            <Link
              href="/pricing"
              className="text-teal-700 font-medium hover:text-teal-800 underline underline-offset-2 decoration-teal-200 hover:decoration-teal-400 transition-colors"
            >
              See all plans
            </Link>
          </motion.p>
        </div>
      </section>

      {/* ════════════ FINAL CTA ════════════ */}
      <section className="relative py-24 md:py-32 overflow-hidden bg-slate-900">
        {/* Gradient mesh */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute top-0 left-1/4 h-[400px] w-[400px] rounded-full bg-teal-500/10 blur-[100px]" />
          <div className="absolute bottom-0 right-1/4 h-[300px] w-[300px] rounded-full bg-amber-500/10 blur-[100px]" />
        </div>

        <motion.div
          className="container relative mx-auto px-4 text-center"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.4 }}
          variants={reveal}
        >
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
            Your meetings deserve better.
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-lg mx-auto">
            Join hundreds of teams who stopped taking notes
            and started shipping faster.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Button
              size="lg"
              asChild
              className="group bg-teal-500 hover:bg-teal-400 text-white px-8 h-13 text-base rounded-xl shadow-lg shadow-teal-500/25 transition-all duration-200"
            >
              <Link href="/signup">
                Get started free
                <ArrowRight className="ml-2 h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Link>
            </Button>
          </div>
          <p className="mt-4 text-sm text-slate-500">
            Free forever for 10 meetings/month. No credit card needed.
          </p>
        </motion.div>
      </section>
    </div>
  );
}
