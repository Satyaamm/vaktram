"use client";

import { motion } from "framer-motion";
import { Sparkles, Bot, Brain, Calendar, Search, Mic } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const releases = [
  {
    version: "0.9.0",
    date: "March 2026",
    title: "Polish & Deploy",
    icon: Sparkles,
    changes: [
      "Password reset flow with email verification",
      "Complete marketing pages (About, Contact, Blog, Docs, etc.)",
      "Custom SMTP for transactional emails",
      "Auto-create user profiles on first authentication",
    ],
  },
  {
    version: "0.8.0",
    date: "February 2026",
    title: "Calendar Integration",
    icon: Calendar,
    changes: [
      "Google Calendar OAuth connection",
      "Auto-sync upcoming meetings",
      "One-click calendar disconnect",
      "Meeting scheduling from dashboard",
    ],
  },
  {
    version: "0.7.0",
    date: "February 2026",
    title: "Full Frontend Pages",
    icon: Search,
    changes: [
      "12 dashboard pages fully implemented",
      "Meeting detail view with transcript, summary, and action items",
      "Semantic search across all meetings",
      "Analytics dashboard with charts",
    ],
  },
  {
    version: "0.6.0",
    date: "January 2026",
    title: "End-to-End Pipeline",
    icon: Brain,
    changes: [
      "Summarization worker with LiteLLM router",
      "Vector embeddings for semantic search (pgvector)",
      "WebSocket real-time transcript streaming",
      "Frontend meeting recording components",
    ],
  },
  {
    version: "0.5.0",
    date: "January 2026",
    title: "Transcription Engine",
    icon: Mic,
    changes: [
      "Faster-Whisper transcription pipeline",
      "Speaker diarization with pyannote.audio",
      "Chunked audio processing for long meetings",
      "Transcript segment storage with timestamps",
    ],
  },
  {
    version: "0.4.0",
    date: "December 2025",
    title: "Meeting Bot Service",
    icon: Bot,
    changes: [
      "Playwright-based meeting bot for Google Meet, Zoom, and Teams",
      "PulseAudio virtual audio capture",
      "FFmpeg audio encoding pipeline",
      "Bot orchestrator with session management",
    ],
  },
];

export default function ChangelogPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-b from-slate-900 to-slate-800 text-white py-24 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <motion.h1
            className="text-4xl md:text-5xl font-bold tracking-tight"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={0}
          >
            Changelog
          </motion.h1>
          <motion.p
            className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
          >
            A history of everything we&apos;ve shipped. Follow along as we build
            the future of meeting intelligence.
          </motion.p>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-3xl">
          <div className="relative border-l-2 border-slate-200 ml-6 space-y-12">
            {releases.map((release, i) => (
              <motion.div
                key={release.version}
                className="relative pl-10"
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
              >
                {/* Timeline dot */}
                <div className="absolute -left-[21px] top-0 flex h-10 w-10 items-center justify-center rounded-full bg-teal-700 text-white shadow-md">
                  <release.icon className="h-5 w-5" />
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-mono font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                      v{release.version}
                    </span>
                    <span className="text-sm text-slate-400">
                      {release.date}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">
                    {release.title}
                  </h3>
                  <ul className="mt-3 space-y-1.5">
                    {release.changes.map((change) => (
                      <li
                        key={change}
                        className="text-sm text-slate-600 flex items-start gap-2"
                      >
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />
                        {change}
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
