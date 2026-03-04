"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const methodColors: Record<string, string> = {
  GET: "bg-emerald-100 text-emerald-800",
  POST: "bg-blue-100 text-blue-800",
  PATCH: "bg-amber-100 text-amber-800",
  DELETE: "bg-red-100 text-red-800",
};

const endpoints = [
  {
    category: "Meetings",
    items: [
      {
        method: "GET",
        path: "/api/v1/meetings",
        description: "List all meetings for the authenticated user",
      },
      {
        method: "GET",
        path: "/api/v1/meetings/:id",
        description: "Get a single meeting with transcript and summary",
      },
      {
        method: "POST",
        path: "/api/v1/meetings",
        description: "Create a new meeting record",
      },
      {
        method: "DELETE",
        path: "/api/v1/meetings/:id",
        description: "Delete a meeting and all associated data",
      },
    ],
  },
  {
    category: "Transcripts",
    items: [
      {
        method: "GET",
        path: "/api/v1/meetings/:id/transcript",
        description: "Get the full transcript with speaker labels and timestamps",
      },
      {
        method: "GET",
        path: "/api/v1/meetings/:id/transcript/segments",
        description: "Get individual transcript segments",
      },
    ],
  },
  {
    category: "Summaries",
    items: [
      {
        method: "GET",
        path: "/api/v1/meetings/:id/summary",
        description: "Get the AI-generated summary for a meeting",
      },
      {
        method: "POST",
        path: "/api/v1/meetings/:id/summary/regenerate",
        description: "Regenerate the summary using current AI configuration",
      },
    ],
  },
  {
    category: "Search",
    items: [
      {
        method: "POST",
        path: "/api/v1/search",
        description: "Semantic search across all meetings (uses pgvector)",
      },
    ],
  },
  {
    category: "Teams",
    items: [
      {
        method: "GET",
        path: "/api/v1/teams/profile",
        description: "Get the authenticated user's profile",
      },
      {
        method: "PATCH",
        path: "/api/v1/teams/profile",
        description: "Update the authenticated user's profile",
      },
      {
        method: "GET",
        path: "/api/v1/teams/organization",
        description: "Get the user's organization details",
      },
      {
        method: "GET",
        path: "/api/v1/teams/members",
        description: "List all members of the organization",
      },
    ],
  },
  {
    category: "AI Configuration",
    items: [
      {
        method: "GET",
        path: "/api/v1/ai-config",
        description: "Get the user's AI model configuration",
      },
      {
        method: "POST",
        path: "/api/v1/ai-config",
        description: "Create or update AI model configuration (BYOM)",
      },
    ],
  },
  {
    category: "Bot",
    items: [
      {
        method: "POST",
        path: "/api/v1/bot/join",
        description: "Send the bot to join a meeting by URL",
      },
      {
        method: "POST",
        path: "/api/v1/bot/leave",
        description: "Tell the bot to leave the current meeting",
      },
      {
        method: "GET",
        path: "/api/v1/bot/status/:session_id",
        description: "Check the status of a bot session",
      },
    ],
  },
];

export default function ApiReferencePage() {
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
            API Reference
          </motion.h1>
          <motion.p
            className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
          >
            The Vaktram REST API. All endpoints require a Bearer token from
            Supabase authentication.
          </motion.p>
        </div>
      </section>

      {/* Auth Info */}
      <section className="py-8 px-4 bg-slate-50 border-b border-slate-200">
        <div className="container mx-auto max-w-4xl">
          <div className="bg-white rounded-lg border border-slate-200 p-5">
            <h3 className="text-sm font-semibold text-slate-900 mb-2">
              Authentication
            </h3>
            <p className="text-sm text-slate-600 mb-3">
              Include the Supabase access token in the Authorization header:
            </p>
            <code className="block bg-slate-900 text-slate-100 text-sm rounded-md px-4 py-3 font-mono">
              Authorization: Bearer {"<your-supabase-access-token>"}
            </code>
          </div>
        </div>
      </section>

      {/* Endpoints */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl space-y-12">
          {endpoints.map((group, i) => (
            <motion.div
              key={group.category}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              custom={i}
            >
              <h2 className="text-xl font-bold text-slate-900 mb-4">
                {group.category}
              </h2>
              <div className="space-y-3">
                {group.items.map((ep) => (
                  <div
                    key={`${ep.method}-${ep.path}`}
                    className="flex items-start gap-4 bg-white border border-slate-200 rounded-lg px-5 py-4"
                  >
                    <Badge
                      className={`font-mono text-xs shrink-0 ${methodColors[ep.method]}`}
                    >
                      {ep.method}
                    </Badge>
                    <div className="min-w-0">
                      <code className="text-sm font-mono text-slate-800 break-all">
                        {ep.path}
                      </code>
                      <p className="text-sm text-slate-500 mt-1">
                        {ep.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
