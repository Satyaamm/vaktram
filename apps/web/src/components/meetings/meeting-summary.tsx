"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  CheckCircle2,
  Circle,
  Clock,
  ListChecks,
  Lightbulb,
  MessageSquareText,
} from "lucide-react";
import type { MeetingSummary as MeetingSummaryType } from "@/types";

const priorityConfig: Record<string, { className: string; label: string }> = {
  high: {
    className: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
    label: "High",
  },
  medium: {
    className:
      "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
    label: "Medium",
  },
  low: {
    className:
      "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
    label: "Low",
  },
};

const statusIcons: Record<string, typeof Circle> = {
  pending: Circle,
  in_progress: Clock,
  completed: CheckCircle2,
};

interface MeetingSummaryProps {
  summary: MeetingSummaryType;
}

export function MeetingSummary({ summary }: MeetingSummaryProps) {
  const topics = summary.topics ?? [];
  const actionItems = summary.action_items ?? [];
  const decisions = summary.key_decisions ?? [];

  return (
    <div className="space-y-6">
      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquareText className="h-5 w-5 text-teal-700" />
            Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {summary.summary_text}
          </p>
        </CardContent>
      </Card>

      {/* Key Topics */}
      {topics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-teal-700" />
              Key Topics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {topics.map((topic: string) => (
                <Badge
                  key={topic}
                  variant="outline"
                  className="border-teal-200 text-teal-800 dark:border-teal-800 dark:text-teal-300"
                >
                  {topic}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Items */}
      {actionItems.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-5 w-5 text-teal-700" />
              Action Items
            </CardTitle>
            <CardDescription>
              {actionItems.length} action item
              {actionItems.length !== 1 ? "s" : ""} identified
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {actionItems.map((rawItem, idx) => {
                const item = rawItem as Record<string, string>;
                const StatusIcon =
                  statusIcons[item.status] ?? Circle;
                const priority =
                  priorityConfig[item.priority] ?? priorityConfig.medium;

                return (
                  <div
                    key={item.id ?? idx}
                    className="flex items-start justify-between rounded-lg border p-4"
                  >
                    <div className="flex items-start gap-3">
                      <StatusIcon className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
                      <div className="space-y-1">
                        <p className="text-sm font-medium">{item.title}</p>
                        {item.description && (
                          <p className="text-xs text-muted-foreground">
                            {item.description}
                          </p>
                        )}
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          {item.assignee_name && (
                            <span>Assigned to {item.assignee_name}</span>
                          )}
                          {item.assignee_name && item.due_date && (
                            <span>&middot;</span>
                          )}
                          {item.due_date && <span>Due {item.due_date}</span>}
                        </div>
                      </div>
                    </div>
                    <Badge variant="secondary" className={priority.className}>
                      {priority.label}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Decisions */}
      {decisions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-teal-700" />
              Decisions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {decisions.map((rawDecision, i) => {
                const decision = rawDecision as Record<string, string>;
                return (
                  <li key={i} className="flex items-start gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-teal-700 shrink-0" />
                    <span className="text-sm text-muted-foreground">
                      {decision.decision ?? decision.text ?? String(rawDecision)}
                    </span>
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Sentiment & Meta */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {summary.sentiment && (
              <>
                <div className="flex items-center gap-1.5">
                  <span>Sentiment:</span>
                  <Badge variant="outline" className="capitalize">
                    {summary.sentiment}
                  </Badge>
                </div>
                <Separator orientation="vertical" className="h-4" />
              </>
            )}
            <span>
              Generated by {summary.model_used ?? "AI"} on{" "}
              {new Date(summary.created_at).toLocaleDateString()}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
