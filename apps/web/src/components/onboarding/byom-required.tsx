"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Brain, ArrowRight } from "lucide-react";
import { aiConfigStatusApi } from "@/lib/api/ai-config-status";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * Strong, hard-to-miss banner that appears anywhere a feature requires the
 * user's BYOM key. Vaktram is pure BYOM — without a key the AI surface is
 * entirely inert (summaries, Vakta, semantic search all fail). The banner
 * intentionally uses warning colors and copy so users can't drift past it.
 *
 * Variants:
 *  - banner: full-width amber strip, used at the top of pages
 *  - card:   centered call-to-action card, used in empty states
 */
export function ByomRequired({
  feature = "AI features",
  variant = "banner",
}: {
  feature?: string;
  variant?: "banner" | "card";
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["ai-config-status"],
    queryFn: aiConfigStatusApi.get,
    staleTime: 60_000,
  });

  if (isLoading || data?.configured) return null;

  const wrapper =
    variant === "banner"
      ? "rounded-lg border-2 border-amber-300 bg-amber-50 p-4 flex items-start gap-3 shadow-sm"
      : "p-6 flex flex-col items-center text-center gap-3 border-2 border-amber-200 bg-amber-50";

  return (
    <Card className={wrapper}>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-200 text-amber-800">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-amber-950">
          AI provider key required to use {feature}
        </p>
        <p className="text-xs text-amber-900 mt-1 leading-relaxed">
          Vaktram is <b>bring-your-own-model</b>. Without your own LLM API key
          (OpenAI, Anthropic, Gemini, Groq, Bedrock, or Vertex AI),
          summaries, Vakta chat, and semantic search will not work. Vaktram
          never charges you for AI usage — you pay your provider directly.
          Your key is encrypted and only used for your own account.
        </p>
      </div>
      <Link href="/settings/ai-config">
        <Button size="sm" className="bg-amber-700 hover:bg-amber-800 text-white shrink-0">
          <Brain className="h-3.5 w-3.5 mr-1" />
          Add AI key
          <ArrowRight className="h-3 w-3 ml-1" />
        </Button>
      </Link>
    </Card>
  );
}
