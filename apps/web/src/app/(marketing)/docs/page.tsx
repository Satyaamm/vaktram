"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Rocket,
  Bot,
  Brain,
  Key,
  Calendar,
  Search,
  Users,
  Settings,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const sections = [
  {
    icon: Rocket,
    title: "Getting Started",
    description: "Create an account, connect your calendar, and record your first meeting in under 5 minutes.",
    steps: [
      "Sign up with Google, Microsoft, or email",
      "Connect your Google Calendar from Settings",
      "Join a meeting — Vaktram's bot joins automatically",
      "View your transcript and AI summary on the dashboard",
    ],
  },
  {
    icon: Brain,
    title: "Bring Your Own Model (BYOM)",
    description: "Use any LLM provider for summarization. Add your API key and choose your preferred model.",
    steps: [
      "Go to Settings → AI Configuration",
      "Add your API key (OpenAI, Anthropic, Google, etc.)",
      "Select your preferred model from the dropdown",
      "All future summaries use your chosen model",
    ],
  },
  {
    icon: Bot,
    title: "Meeting Bot",
    description: "The Vaktram bot joins Google Meet, Zoom, and Microsoft Teams calls to capture audio.",
    steps: [
      "Bot joins automatically for calendar-synced meetings",
      "Or paste a meeting link to send the bot manually",
      "Audio is captured, transcribed, and summarized",
      "Bot leaves when the meeting ends",
    ],
  },
  {
    icon: Search,
    title: "Semantic Search",
    description: "Search across all your meetings using natural language. Find exactly what was discussed.",
    steps: [
      "Use the search bar on the dashboard",
      "Type natural language queries like \"budget discussion last week\"",
      "Results are ranked by semantic relevance",
      "Click any result to jump to that moment in the transcript",
    ],
  },
];

const quickLinks = [
  { icon: Key, label: "API Reference", href: "/api-reference" },
  { icon: Calendar, label: "Calendar Setup", href: "/docs" },
  { icon: Users, label: "Team Management", href: "/docs" },
  { icon: Settings, label: "Settings Guide", href: "/docs" },
];

export default function DocsPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-950 to-blue-900 text-white py-24 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <motion.h1
            className="text-4xl md:text-5xl font-bold tracking-tight"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={0}
          >
            Documentation
          </motion.h1>
          <motion.p
            className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
          >
            Everything you need to get started with Vaktram and make the most of
            AI-powered meeting intelligence.
          </motion.p>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 px-4 border-b border-slate-200">
        <div className="container mx-auto max-w-5xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {quickLinks.map((link, i) => (
              <motion.div
                key={link.label}
                variants={fadeUp}
                initial="hidden"
                animate="visible"
                custom={i}
              >
                <Link
                  href={link.href}
                  className="flex items-center gap-3 rounded-lg border border-slate-200 px-4 py-3 hover:border-teal-300 hover:bg-teal-50/50 transition-colors"
                >
                  <link.icon className="h-5 w-5 text-teal-700" />
                  <span className="text-sm font-medium text-slate-700">
                    {link.label}
                  </span>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Sections */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl space-y-16">
          {sections.map((section, i) => (
            <motion.div
              key={section.title}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              custom={i}
            >
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-teal-700/10 text-teal-700">
                  <section.icon className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">
                    {section.title}
                  </h2>
                  <p className="mt-2 text-slate-600 leading-relaxed">
                    {section.description}
                  </p>
                  <ol className="mt-4 space-y-2">
                    {section.steps.map((step, j) => (
                      <li
                        key={j}
                        className="flex items-start gap-3 text-sm text-slate-600"
                      >
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">
                          {j + 1}
                        </span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
