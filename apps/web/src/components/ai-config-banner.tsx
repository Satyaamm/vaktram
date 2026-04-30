"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import Link from "next/link";

import { getAIConfigs } from "@/lib/api/settings";
import { useAuthStore } from "@/lib/stores/auth-store";
import type { UserAIConfig } from "@/types";

export function AIConfigBanner() {
  const { accessToken } = useAuthStore();

  const { data: configs, isLoading } = useQuery<UserAIConfig[]>({
    queryKey: ["ai-configs"],
    queryFn: getAIConfigs,
    enabled: !!accessToken,
    staleTime: 60_000,
  });

  // Don't show while loading or if user has at least one active config
  if (isLoading || !configs || configs.some((c) => c.is_active)) return null;

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2.5 dark:border-amber-800 dark:bg-amber-950">
      <div className="flex items-center justify-center gap-2 text-sm text-amber-800 dark:text-amber-200">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          AI features are disabled. You need to{" "}
          <Link
            href="/settings/ai-config"
            className="font-semibold underline underline-offset-2 hover:text-amber-900 dark:hover:text-amber-100"
          >
            configure an AI model
          </Link>{" "}
          to enable meeting summaries, action items, and insights.
        </span>
      </div>
    </div>
  );
}
