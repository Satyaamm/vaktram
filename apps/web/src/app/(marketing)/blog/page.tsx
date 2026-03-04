"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const posts = [
  {
    slug: "introducing-vaktram",
    title: "Introducing Vaktram: AI Meeting Notes, Your Way",
    excerpt:
      "Today we're launching Vaktram — the first meeting intelligence platform that lets you bring your own AI model. Here's why BYOM matters.",
    date: "Mar 1, 2026",
    category: "Announcements",
  },
  {
    slug: "byom-explained",
    title: "BYOM Explained: Why Bring Your Own Model Changes Everything",
    excerpt:
      "Most meeting tools force you into one AI provider. We think you deserve better. Learn how BYOM gives you control over privacy, cost, and quality.",
    date: "Feb 20, 2026",
    category: "Product",
  },
  {
    slug: "meeting-productivity-tips",
    title: "5 Ways AI Meeting Notes Boost Team Productivity",
    excerpt:
      "Meetings don't have to be productivity killers. Here's how automatic transcription and smart summaries keep your team moving faster.",
    date: "Feb 10, 2026",
    category: "Tips",
  },
  {
    slug: "gemini-flash-integration",
    title: "Free AI Summaries with Gemini 2.0 Flash",
    excerpt:
      "Getting started with Vaktram costs nothing. We walk through how the default Gemini 2.0 Flash integration works and what you can expect.",
    date: "Jan 28, 2026",
    category: "Tutorials",
  },
];

export default function BlogPage() {
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
            Blog
          </motion.h1>
          <motion.p
            className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
          >
            Product updates, tips, and insights on AI-powered meeting
            productivity.
          </motion.p>
        </div>
      </section>

      {/* Posts */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl space-y-8">
          {posts.map((post, i) => (
            <motion.article
              key={post.slug}
              className="group bg-white rounded-xl border border-slate-200 p-8 hover:shadow-md transition-shadow"
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              custom={i}
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="text-xs font-medium text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full">
                  {post.category}
                </span>
                <span className="text-sm text-slate-400">{post.date}</span>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 group-hover:text-teal-700 transition-colors">
                {post.title}
              </h2>
              <p className="mt-2 text-slate-600 leading-relaxed">
                {post.excerpt}
              </p>
              <Link
                href="#"
                className="inline-flex items-center gap-1 mt-4 text-sm font-medium text-teal-700 hover:gap-2 transition-all"
              >
                Read more <ArrowRight className="h-4 w-4" />
              </Link>
            </motion.article>
          ))}
        </div>
      </section>
    </div>
  );
}
