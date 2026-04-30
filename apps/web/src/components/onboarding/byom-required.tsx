"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Brain, ArrowRight } from "lucide-react";
import { aiConfigStatusApi } from "@/lib/api/ai-config-status";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * Soft banner that appears anywhere a feature requires the user's BYOM key.
 * Pass `feature` to customize the copy ("summaries", "Vakta", "semantic search").
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
      ? "rounded-lg border border-amber-200 bg-amber-50 p-4 flex items-start gap-3"
      : "p-6 flex flex-col items-center text-center gap-3";

  return (
    <Card className={wrapper}>
      <Brain className="h-6 w-6 text-amber-700 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">
          Plug in your AI provider to use {feature}.
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          Vaktram is BYOM — bring your own OpenAI, Anthropic, Gemini, Groq, or
          Bedrock key. Your key is encrypted and only used for your account.
        </p>
      </div>
      <Link href="/settings/ai-config">
        <Button size="sm" className="bg-teal-700 hover:bg-teal-800 text-white">
          Configure AI
          <ArrowRight className="h-3 w-3 ml-1" />
        </Button>
      </Link>
    </Card>
  );
}
