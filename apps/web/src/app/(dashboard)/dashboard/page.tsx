"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Video, Clock, CheckSquare, Users } from "lucide-react";
import { useMeetings } from "@/lib/hooks/use-meeting";
import {
  getAnalyticsOverview,
  getTeamMembers,
  type AnalyticsOverview,
  type TeamMember,
} from "@/lib/api/settings";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { WelcomeBanner } from "@/components/onboarding/welcome-banner";
import { ByomRequired } from "@/components/onboarding/byom-required";
import type { Meeting } from "@/types";

function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return `Today, ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }
  if (diffDays === 1) {
    return `Yesterday, ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }
  return date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function platformIcon(platform: Meeting["platform"]): string {
  switch (platform) {
    case "zoom":
      return "Zoom";
    case "google_meet":
      return "Meet";
    case "teams":
      return "Teams";
    default:
      return "Other";
  }
}

function statusBadge(status: Meeting["status"]) {
  switch (status) {
    case "completed":
      return (
        <Badge variant="secondary" className="bg-teal-100 text-teal-800">
          Completed
        </Badge>
      );
    case "in_progress":
      return (
        <Badge className="bg-amber-100 text-amber-800">In Progress</Badge>
      );
    case "scheduled":
      return (
        <Badge variant="outline" className="border-blue-300 text-blue-700">
          Scheduled
        </Badge>
      );
    case "cancelled":
      return (
        <Badge variant="outline" className="border-red-300 text-red-700">
          Cancelled
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function StatsLoadingSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-4" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-16 mb-1" />
            <Skeleton className="h-3 w-28" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function MeetingsLoadingSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-lg border p-4"
        >
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-64" />
          </div>
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const {
    data: meetings,
    isLoading: meetingsLoading,
  } = useMeetings({ limit: 5 });

  const {
    data: analytics,
    isLoading: analyticsLoading,
  } = useQuery<AnalyticsOverview>({
    queryKey: ["analytics", "overview"],
    queryFn: getAnalyticsOverview,
    retry: 1,
  });

  const { data: teamMembers } = useQuery<TeamMember[]>({
    queryKey: ["team", "members"],
    queryFn: getTeamMembers,
    retry: false,
  });

  const isStatsLoading = analyticsLoading;

  const stats = [
    {
      title: "Total Meetings",
      value: analytics?.total_meetings ?? 0,
      description: `${analytics?.meetings_this_week ?? 0} this week`,
      icon: Video,
    },
    {
      title: "Hours Recorded",
      value: analytics
        ? `${Math.round(analytics.total_duration_hours * 10) / 10}h`
        : "0h",
      description: `${analytics?.meetings_this_week ?? 0} this week`,
      icon: Clock,
    },
    {
      title: "Avg Duration",
      value: analytics
        ? `${Math.round(analytics.avg_duration_minutes)}m`
        : "0m",
      description: "per meeting",
      icon: CheckSquare,
    },
    {
      title: "Team Members",
      value: teamMembers?.length ?? 0,
      description: `${teamMembers?.filter((m) => m.role === "admin" || m.role === "owner").length ?? 0} admins`,
      icon: Users,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome to Vaktram
        </h1>
        <p className="text-muted-foreground mt-1">
          Your AI-powered meeting intelligence dashboard.
        </p>
      </div>

      <ByomRequired feature="summaries, Vakta, and semantic search" />
      <WelcomeBanner />

      {/* Stats Grid */}
      {isStatsLoading ? (
        <StatsLoadingSkeleton />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-teal-700 dark:text-teal-500">
                  {stat.value}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Recent Meetings */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Meetings</CardTitle>
          <CardDescription>
            Your latest recorded and transcribed meetings.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {meetingsLoading ? (
            <MeetingsLoadingSkeleton />
          ) : !meetings || meetings.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Video className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground">
                No meetings yet. Start by recording your first meeting.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {meetings.map((meeting) => (
                <Link
                  key={meeting.id}
                  href={`/meetings/${meeting.id}`}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50 cursor-pointer"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {meeting.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(meeting.created_at)} &middot;{" "}
                      {meeting.duration_seconds
                        ? formatDuration(meeting.duration_seconds)
                        : "N/A"}{" "}
                      &middot; {platformIcon(meeting.platform)} &middot;{" "}
                      {meeting.participants?.length ?? 0} participants
                    </p>
                  </div>
                  {statusBadge(meeting.status)}
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
