"use client";

import { motion } from "framer-motion";

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
    title: "1. Information We Collect",
    content: `When you create an account, we collect your name, email address, and authentication credentials. When you use Vaktram to record meetings, we process meeting audio, generate transcripts, and create AI summaries. If you use the BYOM (Bring Your Own Model) feature, your API keys are encrypted at rest and never logged.`,
  },
  {
    title: "2. How We Use Your Information",
    content: `We use your information to provide and improve the Vaktram service, including: transcribing and summarizing your meetings, enabling search across your meeting history, syncing with your calendar, and sending transactional emails (verification, password resets). We do not sell your data to third parties.`,
  },
  {
    title: "3. Data Storage & Security",
    content: `Your data is stored in Supabase (PostgreSQL) with row-level security enabled. Meeting audio files are stored in Supabase Storage with access controls. All data is encrypted in transit (TLS) and at rest. API keys you provide for BYOM are encrypted using AES-256 before storage.`,
  },
  {
    title: "4. Third-Party Services",
    content: `Vaktram integrates with third-party services to provide its functionality: Supabase (authentication and database), Google Calendar API (calendar sync), and your chosen LLM provider when using BYOM. Each of these services has its own privacy policy. When using the default Gemini model, meeting content is sent to Google's API for summarization.`,
  },
  {
    title: "5. Your Rights",
    content: `You have the right to: access all data we hold about you, export your meeting data (transcripts and summaries), request deletion of your account and all associated data, and opt out of non-essential communications. To exercise any of these rights, contact us at support@vaktram.com.`,
  },
  {
    title: "6. Data Retention",
    content: `We retain your meeting data for as long as your account is active. When you delete a meeting, it is permanently removed within 30 days. When you delete your account, all associated data is permanently deleted within 30 days.`,
  },
  {
    title: "7. Cookies",
    content: `We use essential cookies for authentication and session management. We do not use tracking cookies or third-party advertising cookies.`,
  },
  {
    title: "8. Changes to This Policy",
    content: `We may update this privacy policy from time to time. We will notify you of significant changes via email or an in-app notification. Continued use of Vaktram after changes constitutes acceptance of the updated policy.`,
  },
  {
    title: "9. Contact",
    content: `If you have questions about this privacy policy, contact us at support@vaktram.com.`,
  },
];

export default function PrivacyPage() {
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
            Privacy Policy
          </motion.h1>
          <motion.p
            className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
          >
            Last updated: March 1, 2026
          </motion.p>
        </div>
      </section>

      {/* Content */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-3xl space-y-10">
          <motion.p
            className="text-slate-600 leading-relaxed"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            At Vaktram, we take your privacy seriously. This policy explains what
            data we collect, how we use it, and your rights regarding your
            information.
          </motion.p>

          {sections.map((section, i) => (
            <motion.div
              key={section.title}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              custom={i}
            >
              <h2 className="text-xl font-semibold text-slate-900 mb-3">
                {section.title}
              </h2>
              <p className="text-slate-600 leading-relaxed">
                {section.content}
              </p>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
