"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CalendarDays, Brain, Sparkles, X, Check } from "lucide-react";

const STORAGE_KEY = "vaktram_welcome_banner_dismissed";

interface Step {
  href: string;
  icon: React.ElementType;
  title: string;
  body: string;
  cta: string;
}

const STEPS: Step[] = [
  {
    href: "/settings/ai-config",
    icon: Brain,
    title: "Plug in your LLM key",
    body: "Bring your own model — OpenAI, Anthropic, Gemini, Groq, or Bedrock. Required to enable summaries, Vakta, and semantic search.",
    cta: "Configure",
  },
  {
    href: "/settings",
    icon: CalendarDays,
    title: "Connect your calendar",
    body: "We auto-join scheduled meetings — Meet, Zoom, and Teams.",
    cta: "Connect",
  },
  {
    href: "/ask",
    icon: Sparkles,
    title: "Try Ask Vakta",
    body: "Chat with your meetings — ask anything, get cited answers.",
    cta: "Open",
  },
];

export function WelcomeBanner() {
  const [hidden, setHidden] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setHidden(window.localStorage.getItem(STORAGE_KEY) === "1");
  }, []);

  if (hidden) return null;

  const dismiss = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // ignore
    }
    setHidden(true);
  };

  return (
    <Card className="relative bg-gradient-to-br from-teal-50 to-white border-teal-100">
      <button
        onClick={dismiss}
        aria-label="Dismiss welcome"
        className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </button>
      <div className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Check className="h-5 w-5 text-teal-700" />
          <p className="font-semibold">You're set up. Three things to make Vaktram sing:</p>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {STEPS.map((s) => (
            <div
              key={s.href}
              className="flex items-start gap-3 rounded-md border bg-white p-3"
            >
              <s.icon className="h-5 w-5 text-teal-700 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-medium">{s.title}</p>
                <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                  {s.body}
                </p>
                <Link
                  href={s.href}
                  className="text-xs text-teal-700 hover:underline mt-1 inline-block"
                >
                  {s.cta} →
                </Link>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex justify-end">
          <Button variant="ghost" size="sm" onClick={dismiss}>
            Don&apos;t show again
          </Button>
        </div>
      </div>
    </Card>
  );
}
