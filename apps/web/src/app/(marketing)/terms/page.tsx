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
    title: "1. Acceptance of Terms",
    content: `By accessing or using Vaktram ("the Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service. These terms apply to all users, including free and paid plan subscribers.`,
  },
  {
    title: "2. Description of Service",
    content: `Vaktram is an AI-powered meeting intelligence platform that provides meeting recording, transcription, summarization, and semantic search. The Service includes a web application, API, and meeting bot that joins video conferencing platforms on your behalf.`,
  },
  {
    title: "3. Account Registration",
    content: `You must provide accurate and complete information when creating an account. You are responsible for maintaining the security of your account credentials. You must be at least 18 years old or have the consent of a legal guardian to use the Service.`,
  },
  {
    title: "4. Acceptable Use",
    content: `You agree not to: record meetings without the knowledge and consent of all participants where required by law, use the Service for any illegal purpose, attempt to reverse-engineer the Service, share your account with unauthorized users, or use the Service to harass, abuse, or harm others.`,
  },
  {
    title: "5. Meeting Recording Consent",
    content: `You are solely responsible for obtaining consent from all meeting participants before recording. Vaktram's bot will identify itself when joining meetings, but the legal obligation to obtain consent rests with you. Recording laws vary by jurisdiction — ensure you comply with all applicable laws.`,
  },
  {
    title: "6. BYOM (Bring Your Own Model)",
    content: `When you use the BYOM feature, you provide your own API keys for third-party AI services. You are responsible for compliance with those services' terms of use. Vaktram encrypts your API keys but is not responsible for charges incurred on your third-party accounts.`,
  },
  {
    title: "7. Data Ownership",
    content: `You retain ownership of all content generated from your meetings (transcripts, summaries, etc.). By using the Service, you grant Vaktram a limited license to process your content solely for the purpose of providing the Service. We do not use your content to train AI models.`,
  },
  {
    title: "8. Pricing & Billing",
    content: `Free accounts are limited as described on our Pricing page. Paid plans are billed monthly or annually. You may cancel at any time; your access continues through the end of the billing period. Refunds are provided at our discretion.`,
  },
  {
    title: "9. Service Availability",
    content: `We strive for high availability but do not guarantee uninterrupted service. We may perform maintenance with reasonable notice. We reserve the right to modify or discontinue features with notice.`,
  },
  {
    title: "10. Limitation of Liability",
    content: `To the maximum extent permitted by law, Vaktram shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the Service. Our total liability shall not exceed the amount you paid us in the 12 months preceding the claim.`,
  },
  {
    title: "11. Termination",
    content: `We may suspend or terminate your account if you violate these terms. You may delete your account at any time from the Settings page. Upon termination, your data will be deleted in accordance with our Privacy Policy.`,
  },
  {
    title: "12. Changes to Terms",
    content: `We may update these terms from time to time. We will notify you of material changes via email or in-app notification. Continued use after changes constitutes acceptance.`,
  },
  {
    title: "13. Contact",
    content: `For questions about these terms, contact us at support@vaktram.com.`,
  },
];

export default function TermsPage() {
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
            Terms of Service
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
            Please read these Terms of Service carefully before using Vaktram.
            These terms govern your use of our platform and services.
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
