"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, ChevronDown } from "lucide-react";
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

const tiers = [
  {
    key: "free" as const,
    description: "For individuals getting started",
    cta: "Get Started",
    monthlyPrice: 0,
    annualPrice: 0,
    highlight: false,
  },
  {
    key: "pro" as const,
    description: "For professionals who need more",
    cta: "Start Free Trial",
    monthlyPrice: 19,
    annualPrice: 15,
    highlight: true,
  },
  {
    key: "team" as const,
    description: "For growing teams",
    cta: "Start Free Trial",
    monthlyPrice: 49,
    annualPrice: 39,
    highlight: false,
  },
  {
    key: "enterprise" as const,
    description: "For large organizations",
    cta: "Contact Sales",
    monthlyPrice: -1,
    annualPrice: -1,
    highlight: false,
  },
];

const allFeatures = [
  { label: "Basic transcription", free: true, pro: true, team: true, enterprise: true },
  { label: "AI summaries (BYOM)", free: true, pro: true, team: true, enterprise: true },
  { label: "5 meetings/month", free: true, pro: false, team: false, enterprise: false },
  { label: "100 meetings/month", free: false, pro: true, team: false, enterprise: false },
  { label: "Unlimited meetings", free: false, pro: false, team: true, enterprise: true },
  { label: "Calendar integration", free: false, pro: true, team: true, enterprise: true },
  { label: "Search across meetings", free: false, pro: true, team: true, enterprise: true },
  { label: "AI action items", free: false, pro: true, team: true, enterprise: true },
  { label: "Team analytics", free: false, pro: false, team: true, enterprise: true },
  { label: "Shared meeting library", free: false, pro: false, team: true, enterprise: true },
  { label: "Admin controls", free: false, pro: false, team: true, enterprise: true },
  { label: "Priority support", free: false, pro: false, team: true, enterprise: true },
  { label: "SSO / SAML", free: false, pro: false, team: false, enterprise: true },
  { label: "Custom integrations", free: false, pro: false, team: false, enterprise: true },
  { label: "On-prem deployment", free: false, pro: false, team: false, enterprise: true },
  { label: "SLA guarantee", free: false, pro: false, team: false, enterprise: true },
];

const faqs = [
  {
    question: "What is BYOM?",
    answer:
      "BYOM stands for Bring Your Own Model. It means you can connect your own AI provider (OpenAI, Anthropic, Google, Azure, Ollama, or any OpenAI-compatible API) using your own API keys. Your data stays under your control, and you choose which model processes your meetings.",
  },
  {
    question: "Can I use my own API key?",
    answer:
      "Yes! All plans support BYOM. You provide your own API key, and it is encrypted at rest and never shared. Vaktram sends your meeting data directly to your chosen provider, so we never store or process your content on our servers.",
  },
  {
    question: "Is there a free trial?",
    answer:
      "The Free plan is free forever with up to 5 meetings per month. For Pro and Team plans, we offer a 14-day free trial with full access to all features. No credit card required to start.",
  },
  {
    question: "How does billing work?",
    answer:
      "We offer monthly and annual billing. Annual plans save you 20%. You can upgrade, downgrade, or cancel at any time. If you cancel, you retain access until the end of your current billing period.",
  },
];

/* ──────────────────────── FAQ Accordion Item ──────────────────────── */

function FaqItem({
  question,
  answer,
}: {
  question: string;
  answer: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-slate-200">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left text-base font-medium text-slate-800 hover:text-teal-700 transition-colors"
      >
        {question}
        <ChevronDown
          className={`h-5 w-5 shrink-0 text-slate-400 transition-transform duration-300 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-sm text-slate-600 leading-relaxed pr-8">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ──────────────────────── page ──────────────────────── */

export default function PricingPage() {
  const [annual, setAnnual] = useState(false);

  return (
    <div className="scroll-smooth">
      {/* Header */}
      <section className="pt-20 pb-8">
        <div className="container mx-auto px-4 text-center">
          <motion.h1
            className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            Choose your plan
          </motion.h1>
          <motion.p
            className="mt-4 text-lg text-slate-600 max-w-xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.5 }}
          >
            Start free, upgrade as you grow. All plans include BYOM support.
          </motion.p>

          {/* Toggle */}
          <motion.div
            className="mt-8 inline-flex items-center gap-3 rounded-full bg-slate-100 p-1.5"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <button
              onClick={() => setAnnual(false)}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-all duration-200 ${
                !annual
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-800"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={`rounded-full px-5 py-2 text-sm font-medium transition-all duration-200 ${
                annual
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-800"
              }`}
            >
              Annual
              <span className="ml-1.5 text-xs font-semibold text-teal-700">
                -20%
              </span>
            </button>
          </motion.div>
        </div>
      </section>

      {/* Pricing cards */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <motion.div
            className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto"
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
          >
            {tiers.map((tier, i) => {
              const plan = PLAN_LIMITS[tier.key];
              const isEnterprise = tier.key === "enterprise";
              const price = isEnterprise
                ? null
                : annual
                ? tier.annualPrice
                : tier.monthlyPrice;

              return (
                <motion.div
                  key={tier.key}
                  variants={fadeUp}
                  custom={i}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  className={`relative rounded-2xl border bg-white p-8 shadow-sm transition-shadow hover:shadow-lg flex flex-col ${
                    tier.highlight
                      ? "border-teal-700 border-2 shadow-lg"
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

                  <h3 className="text-xl font-semibold">{plan.name}</h3>
                  <p className="text-sm text-slate-500 mt-1">
                    {tier.description}
                  </p>

                  <div className="mt-5 mb-6">
                    {isEnterprise ? (
                      <span className="text-4xl font-bold text-slate-800">
                        Custom
                      </span>
                    ) : (
                      <>
                        <span className="text-5xl font-bold text-teal-700">
                          ${price}
                        </span>
                        <span className="text-slate-500 ml-1">/month</span>
                        {annual && tier.monthlyPrice > 0 && (
                          <p className="text-xs text-slate-400 mt-1">
                            <span className="line-through">
                              ${tier.monthlyPrice}/mo
                            </span>{" "}
                            billed annually
                          </p>
                        )}
                      </>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {plan.features.map((f) => (
                      <li
                        key={f}
                        className="flex items-start gap-2.5 text-sm"
                      >
                        <Check className="h-4 w-4 shrink-0 mt-0.5 text-teal-700" />
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
                    <Link href={isEnterprise ? "#" : "/signup"}>
                      {tier.cta}
                    </Link>
                  </Button>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* Feature comparison table */}
      <section className="py-16 bg-slate-50">
        <div className="container mx-auto px-4">
          <motion.h2
            className="text-2xl font-bold text-center mb-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            Compare plans
          </motion.h2>

          <motion.div
            className="max-w-4xl mx-auto overflow-x-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="py-3 pr-4 text-left font-medium text-slate-500 w-1/3">
                    Feature
                  </th>
                  <th className="py-3 px-4 text-center font-medium text-slate-500">
                    Free
                  </th>
                  <th className="py-3 px-4 text-center font-semibold text-teal-700">
                    Pro
                  </th>
                  <th className="py-3 px-4 text-center font-medium text-slate-500">
                    Team
                  </th>
                  <th className="py-3 pl-4 text-center font-medium text-slate-500">
                    Enterprise
                  </th>
                </tr>
              </thead>
              <tbody>
                {allFeatures.map((f) => (
                  <tr
                    key={f.label}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-3 pr-4 text-slate-700">{f.label}</td>
                    {(
                      ["free", "pro", "team", "enterprise"] as const
                    ).map((plan) => (
                      <td key={plan} className="py-3 px-4 text-center">
                        {f[plan] ? (
                          <Check className="h-4 w-4 text-teal-700 mx-auto" />
                        ) : (
                          <X className="h-4 w-4 text-slate-300 mx-auto" />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <motion.h2
            className="text-2xl font-bold text-center mb-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            Frequently asked questions
          </motion.h2>

          <motion.div
            className="max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            {faqs.map((faq) => (
              <FaqItem
                key={faq.question}
                question={faq.question}
                answer={faq.answer}
              />
            ))}
          </motion.div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-20 bg-slate-900">
        <motion.div
          className="container mx-auto px-4 text-center"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.7 }}
        >
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to get started?
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-lg mx-auto">
            Start free and upgrade when you need more. No credit card required.
          </p>
          <Button
            size="lg"
            asChild
            className="mt-8 bg-teal-500 hover:bg-teal-400 text-white px-10 h-14 text-lg rounded-xl shadow-lg shadow-teal-500/30"
          >
            <Link href="/signup">Get Started Free</Link>
          </Button>
        </motion.div>
      </section>
    </div>
  );
}
