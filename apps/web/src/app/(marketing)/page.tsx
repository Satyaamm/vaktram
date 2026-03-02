"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  FileText,
  Cpu,
  Search,
  Calendar,
  Users,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Video,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PLAN_LIMITS } from "@/lib/constants";

/* ──────────────────────── animation helpers ──────────────────────── */

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

/* ──────────────────────── data ──────────────────────── */

const features = [
  {
    icon: Mic,
    title: "Smart Transcription",
    description:
      "Accurate, speaker-labeled transcription for Zoom, Google Meet, and Microsoft Teams in real time.",
  },
  {
    icon: FileText,
    title: "AI Summaries",
    description:
      "Get concise meeting summaries, key decisions, and extracted action items automatically.",
  },
  {
    icon: Cpu,
    title: "BYOM (Bring Your Own Model)",
    description:
      "Use OpenAI, Claude, Gemini, or local models. Your keys, your control, your privacy.",
  },
  {
    icon: Search,
    title: "Semantic Search",
    description:
      "Search across all your meetings using natural language. Find anything said in any meeting.",
  },
  {
    icon: Calendar,
    title: "Calendar Sync",
    description:
      "Connect Google Calendar or Outlook to automatically join and record scheduled meetings.",
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description:
      "Share meeting notes, assign action items, and track team productivity across meetings.",
  },
];

const byomProviders = [
  "OpenAI",
  "Claude",
  "Gemini",
  "Groq",
  "Azure",
  "Ollama",
];

const howItWorks = [
  {
    step: 1,
    icon: Calendar,
    title: "Connect Calendar",
    description:
      "Link your Google or Outlook calendar. Vaktram detects upcoming meetings automatically.",
  },
  {
    step: 2,
    icon: Video,
    title: "Bot Joins Meeting",
    description:
      "Our bot joins on time, records audio, and transcribes every word with speaker labels.",
  },
  {
    step: 3,
    icon: Sparkles,
    title: "Get AI Summary",
    description:
      "Receive a structured summary with action items, decisions, and follow-ups in seconds.",
  },
];

const pricingTiers = [
  { key: "free" as const, cta: "Get Started", highlight: false },
  { key: "pro" as const, cta: "Start Free Trial", highlight: true },
  { key: "team" as const, cta: "Start Free Trial", highlight: false },
];

/* ──────────────────────── page ──────────────────────── */

export default function LandingPage() {
  const [currentProvider, setCurrentProvider] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentProvider((p) => (p + 1) % byomProviders.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="scroll-smooth">
      {/* ───── HERO ───── */}
      <section className="relative overflow-hidden py-28 md:py-40">
        {/* Gradient orb */}
        <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-teal-400/30 via-amber-300/20 to-teal-600/20 blur-3xl" />

        <div className="container relative mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Badge className="mb-6 bg-amber-500 text-white hover:bg-amber-500 px-4 py-1.5 text-sm font-medium shadow-sm">
              Now in Beta
            </Badge>
          </motion.div>

          <motion.h1
            className="text-5xl font-extrabold tracking-tight text-slate-900 sm:text-6xl md:text-7xl lg:text-8xl"
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
          >
            <motion.span variants={fadeUp} custom={0} className="block">
              AI Meeting Notes,
            </motion.span>
            <motion.span
              variants={fadeUp}
              custom={1}
              className="block text-teal-700"
            >
              Your Way
            </motion.span>
          </motion.h1>

          <motion.p
            className="mx-auto mt-8 max-w-2xl text-lg text-slate-600 md:text-xl leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            Record, transcribe, and summarize meetings with your own AI.{" "}
            <span className="font-semibold text-slate-800">
              BYOM — Bring Your Own Model.
            </span>
          </motion.p>

          <motion.div
            className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            <Button
              size="lg"
              asChild
              className="bg-teal-700 hover:bg-teal-800 text-white px-10 h-14 text-lg rounded-xl shadow-lg shadow-teal-700/20"
            >
              <Link href="/signup">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button
              variant="outline"
              size="lg"
              asChild
              className="h-14 text-lg rounded-xl px-8 border-slate-300"
            >
              <Link href="#features">Watch Demo</Link>
            </Button>
          </motion.div>

          <motion.p
            className="mt-5 text-sm text-slate-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
          >
            Free forever for up to 10 meetings/month. No credit card required.
          </motion.p>
        </div>
      </section>

      {/* ───── SOCIAL PROOF ───── */}
      <section className="py-16 border-y border-slate-100 bg-slate-50/50">
        <motion.div
          className="container mx-auto px-4 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.8 }}
        >
          <p className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-8">
            Trusted by teams at
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4">
            {[
              "Acme Corp",
              "Globex",
              "Initech",
              "Umbrella",
              "Stark Industries",
              "Wayne Enterprises",
            ].map((name) => (
              <span
                key={name}
                className="text-xl font-bold text-slate-300 select-none"
              >
                {name}
              </span>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ───── FEATURES ───── */}
      <section id="features" className="py-28 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl md:text-5xl">
              Everything you need for
              <br />
              <span className="text-teal-700">meeting intelligence</span>
            </h2>
            <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
              From recording to action items, Vaktram handles it all while
              keeping you in control of your data.
            </p>
          </motion.div>

          <motion.div
            className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerContainer}
          >
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                custom={i}
                whileHover={{ y: -6, transition: { duration: 0.2 } }}
                className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-sm hover:shadow-lg transition-shadow duration-300"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 group-hover:bg-teal-100 transition-colors duration-200">
                  <feature.icon className="h-6 w-6 text-teal-700" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ───── BYOM ───── */}
      <section id="byom" className="py-28 bg-teal-50">
        <div className="container mx-auto px-4">
          <div className="grid gap-16 lg:grid-cols-2 items-center max-w-6xl mx-auto">
            {/* Left text */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6 }}
            >
              <Badge className="mb-4 bg-amber-500 text-white hover:bg-amber-500">
                BYOM
              </Badge>
              <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl md:text-5xl">
                Your Model,{" "}
                <span className="text-teal-700">Your Rules</span>
              </h2>
              <p className="mt-5 text-lg text-slate-600 leading-relaxed">
                Unlike other tools that lock you into their AI provider, Vaktram
                lets you connect any LLM. Use GPT-4o, Claude, Gemini, or even
                self-hosted models via Ollama.
              </p>
              <ul className="mt-8 space-y-4">
                {[
                  "Use your own API keys -- we never see your data",
                  "Switch providers anytime without losing history",
                  "Run completely offline with local models",
                  "Save costs by choosing the right model for each task",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5 text-teal-700" />
                    <span className="text-slate-700">{item}</span>
                  </li>
                ))}
              </ul>
              <Button
                className="mt-10 bg-teal-700 hover:bg-teal-800 text-white rounded-xl px-8 h-12 text-base shadow-lg shadow-teal-700/20"
                asChild
              >
                <Link href="/signup">
                  Try It Free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </motion.div>

            {/* Right animated providers */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="rounded-2xl border border-teal-200 bg-white p-10 shadow-xl">
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-6">
                  Currently using
                </p>
                <div className="h-20 flex items-center justify-center overflow-hidden">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={byomProviders[currentProvider]}
                      initial={{ opacity: 0, y: 30 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -30 }}
                      transition={{ duration: 0.4 }}
                      className="text-4xl font-bold text-teal-700"
                    >
                      {byomProviders[currentProvider]}
                    </motion.div>
                  </AnimatePresence>
                </div>
                <div className="mt-8 grid grid-cols-3 gap-3">
                  {byomProviders.map((provider, i) => (
                    <div
                      key={provider}
                      className={`rounded-lg border px-3 py-2.5 text-sm text-center font-medium transition-all duration-300 ${
                        i === currentProvider
                          ? "border-teal-700 bg-teal-50 text-teal-700 shadow-sm"
                          : "border-slate-200 text-slate-500"
                      }`}
                    >
                      {provider}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ───── HOW IT WORKS ───── */}
      <section className="py-28 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl md:text-5xl">
              How it works
            </h2>
            <p className="mt-4 text-lg text-slate-600 max-w-xl mx-auto">
              Three simple steps to smarter meetings.
            </p>
          </motion.div>

          <div className="relative max-w-4xl mx-auto">
            {/* Dotted connecting line */}
            <div className="hidden md:block absolute top-24 left-[16.67%] right-[16.67%] border-t-2 border-dashed border-slate-300 z-0" />

            <motion.div
              className="grid gap-8 md:grid-cols-3 relative z-10"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={staggerContainer}
            >
              {howItWorks.map((step, i) => (
                <motion.div
                  key={step.step}
                  variants={fadeUp}
                  custom={i}
                  className="text-center"
                >
                  <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 border-2 border-teal-200">
                    <step.icon className="h-7 w-7 text-teal-700" />
                  </div>
                  <div className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-teal-700 text-white text-sm font-bold mb-4">
                    {step.step}
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed max-w-xs mx-auto">
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* ───── PRICING PREVIEW ───── */}
      <section id="pricing" className="py-28 bg-slate-50">
        <div className="container mx-auto px-4">
          <motion.div
            className="text-center mb-14"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl md:text-5xl">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Start free and scale as your team grows.
            </p>
          </motion.div>

          <motion.div
            className="grid gap-6 md:grid-cols-3 max-w-4xl mx-auto"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerContainer}
          >
            {pricingTiers.map((tier, i) => {
              const plan = PLAN_LIMITS[tier.key];
              return (
                <motion.div
                  key={tier.key}
                  variants={fadeUp}
                  custom={i}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  className={`relative rounded-2xl border bg-white p-8 shadow-sm transition-shadow hover:shadow-lg ${
                    tier.highlight
                      ? "border-teal-700 border-2 shadow-md"
                      : "border-slate-200"
                  }`}
                >
                  {tier.highlight && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <Badge className="bg-teal-700 text-white hover:bg-teal-700 px-4 py-1 shadow-sm">
                        Most Popular
                      </Badge>
                    </div>
                  )}
                  <h3 className="text-lg font-semibold">{plan.name}</h3>
                  <div className="mt-3 mb-6">
                    <span className="text-4xl font-bold text-teal-700">
                      ${plan.price}
                    </span>
                    <span className="text-slate-500">/month</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2.5 text-sm">
                        <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5 text-teal-700" />
                        <span className="text-slate-600">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    asChild
                    className={`w-full rounded-xl h-11 ${
                      tier.highlight
                        ? "bg-teal-700 hover:bg-teal-800 text-white shadow-lg shadow-teal-700/20"
                        : ""
                    }`}
                    variant={tier.highlight ? "default" : "outline"}
                  >
                    <Link href="/signup">{tier.cta}</Link>
                  </Button>
                </motion.div>
              );
            })}
          </motion.div>

          <motion.div
            className="text-center mt-10"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
          >
            <Link
              href="/pricing"
              className="inline-flex items-center gap-2 text-teal-700 font-medium hover:text-teal-800 transition-colors"
            >
              View all plans
              <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ───── CTA ───── */}
      <section className="py-28 bg-slate-900">
        <motion.div
          className="container mx-auto px-4 text-center"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.7 }}
        >
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
            Ready to transform your meetings?
          </h2>
          <p className="mt-5 text-lg text-slate-400 max-w-xl mx-auto">
            Join thousands of teams saving hours every week with AI-powered
            meeting intelligence.
          </p>
          <Button
            size="lg"
            asChild
            className="mt-10 bg-teal-500 hover:bg-teal-400 text-white px-10 h-14 text-lg rounded-xl shadow-lg shadow-teal-500/30"
          >
            <Link href="/signup">
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
          <p className="mt-4 text-sm text-slate-500">
            No credit card required.
          </p>
        </motion.div>
      </section>
    </div>
  );
}
