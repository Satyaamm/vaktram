"use client";

import { motion } from "framer-motion";
import { Users, Target, Zap, Globe } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const values = [
  {
    icon: Target,
    title: "Mission-Driven",
    description:
      "We believe meeting intelligence should be accessible to everyone, not locked behind expensive enterprise contracts.",
  },
  {
    icon: Zap,
    title: "Privacy First",
    description:
      "Your conversations are yours. BYOM means your data never touches our servers — it goes straight to the LLM you choose.",
  },
  {
    icon: Globe,
    title: "Open & Flexible",
    description:
      "No vendor lock-in. Bring your own AI model, switch anytime, and keep full control over your meeting data.",
  },
  {
    icon: Users,
    title: "Team-Centric",
    description:
      "Built for collaboration. Share notes, search across meetings, and keep your entire team aligned effortlessly.",
  },
];

export default function AboutPage() {
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
            About Vaktram
          </motion.h1>
          <motion.p
            className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
          >
            We&apos;re building the meeting intelligence platform that puts you
            in control. No black-box AI — just your meetings, your models, your
            data.
          </motion.p>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl">
          <motion.div
            className="text-center"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={0}
          >
            <h2 className="text-3xl font-bold text-slate-900">Our Mission</h2>
            <p className="mt-6 text-lg text-slate-600 leading-relaxed max-w-3xl mx-auto">
              Meetings are where decisions happen, ideas form, and teams align.
              Yet most of that knowledge vanishes the moment the call ends.
              Vaktram captures, transcribes, and summarizes every meeting —
              using the AI model <em>you</em> trust. We call it{" "}
              <span className="font-semibold text-teal-700">
                Bring Your Own Model (BYOM)
              </span>
              , and it means you never have to compromise on privacy, cost, or
              quality.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 px-4 bg-slate-50">
        <div className="container mx-auto max-w-5xl">
          <motion.h2
            className="text-3xl font-bold text-center text-slate-900 mb-12"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            What We Stand For
          </motion.h2>
          <div className="grid md:grid-cols-2 gap-8">
            {values.map((value, i) => (
              <motion.div
                key={value.title}
                className="bg-white rounded-xl p-8 shadow-sm border border-slate-200"
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-700/10 text-teal-700 mb-4">
                  <value.icon className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900">
                  {value.title}
                </h3>
                <p className="mt-2 text-slate-600 leading-relaxed">
                  {value.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <motion.h2
            className="text-3xl font-bold text-slate-900"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            Built by Engineers, for Teams
          </motion.h2>
          <motion.p
            className="mt-6 text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={1}
          >
            Vaktram is built by a small, focused team passionate about
            productivity and AI. We&apos;ve spent years in the trenches of
            remote work and know firsthand how painful it is to lose context
            from meetings.
          </motion.p>
        </div>
      </section>
    </div>
  );
}
