"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  getAnalyticsOverview,
  getSpeakerTalkTime,
  getMeetingFrequency,
  getTopicFrequency,
  type AnalyticsOverview,
  type SpeakerTalkTime,
  type MeetingFrequency,
  type TopicFrequency,
} from "@/lib/api/settings";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

const TEAL_PALETTE = [
  "#0f766e", // teal-700
  "#14b8a6", // teal-500
  "#2dd4bf", // teal-400
  "#5eead4", // teal-300
  "#99f6e4", // teal-200
  "#134e4a", // teal-900
  "#115e59", // teal-800
  "#0d9488", // teal-600
];

function formatDurationMinutes(minutes: number): string {
  return `${Math.round(minutes)}m`;
}

function MetricCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-16 mb-1" />
        <Skeleton className="h-3 w-24" />
      </CardContent>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-3 w-56 mt-1" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-64 w-full rounded-lg" />
      </CardContent>
    </Card>
  );
}

function OverviewTab() {
  const { data: overview, isLoading } = useQuery<AnalyticsOverview>({
    queryKey: ["analytics", "overview"],
    queryFn: getAnalyticsOverview,
  });

  const { data: frequency, isLoading: freqLoading } = useQuery<
    MeetingFrequency[]
  >({
    queryKey: ["analytics", "frequency", "30d"],
    queryFn: () => getMeetingFrequency("30d"),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <MetricCardSkeleton key={i} />
          ))}
        </div>
        <ChartSkeleton />
      </div>
    );
  }

  const metrics = [
    {
      title: "Total Meetings",
      value: overview?.total_meetings ?? 0,
      sub: `${overview?.meetings_this_week ?? 0} this week`,
    },
    {
      title: "Avg Duration",
      value: overview
        ? formatDurationMinutes(overview.avg_duration_minutes)
        : "--",
      sub: `${overview?.meetings_this_week ?? 0} meetings this week`,
    },
    {
      title: "Total Hours",
      value: overview?.total_duration_hours
        ? Math.round(overview.total_duration_hours * 10) / 10
        : 0,
      sub: "recorded",
    },
  ];

  const chartData = (frequency ?? []).map((item) => ({
    date: new Date(item.date).toLocaleDateString([], {
      month: "short",
      day: "numeric",
    }),
    count: item.count,
  }));

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-teal-700 dark:text-teal-500">
                {metric.value}
              </div>
              <p className="text-xs text-muted-foreground">{metric.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Meeting Trends</CardTitle>
          <CardDescription>
            Meeting frequency over the last 30 days.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {freqLoading ? (
            <Skeleton className="h-64 w-full rounded-lg" />
          ) : chartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center">
              <p className="text-sm text-muted-foreground">
                No data available yet.
              </p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={256}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#0f766e"
                  fill="#14b8a6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                  name="Meetings"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TalkTimeTab() {
  const { data: talkTime, isLoading } = useQuery<SpeakerTalkTime[]>({
    queryKey: ["analytics", "talk-time"],
    queryFn: getSpeakerTalkTime,
  });

  if (isLoading) {
    return <ChartSkeleton />;
  }

  const chartData = (talkTime ?? []).map((item) => ({
    name: item.speaker_name,
    minutes: Math.round(item.total_seconds / 60),
    percentage: item.percentage,
    meetings: item.meeting_count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Talk Time Distribution</CardTitle>
        <CardDescription>
          How speaking time is distributed across team members.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No talk time data available yet.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(256, chartData.length * 48)}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                type="number"
                tick={{ fontSize: 12 }}
                tickLine={false}
                unit="m"
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 12 }}
                tickLine={false}
                width={100}
              />
              <Tooltip
                formatter={(value) => [
                  `${value} min`,
                  "Talk Time",
                ]}
              />
              <Bar dataKey="minutes" radius={[0, 4, 4, 0]}>
                {chartData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index % 2 === 0 ? "#0f766e" : "#14b8a6"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

function FrequencyTab() {
  const [period, setPeriod] = useState("30d");

  const { data: frequency, isLoading } = useQuery<MeetingFrequency[]>({
    queryKey: ["analytics", "frequency", period],
    queryFn: () => getMeetingFrequency(period),
  });

  const chartData = (frequency ?? []).map((item) => ({
    date: new Date(item.date).toLocaleDateString([], {
      month: "short",
      day: "numeric",
    }),
    count: item.count,
  }));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Meeting Frequency</CardTitle>
            <CardDescription>
              Number of meetings over the selected period.
            </CardDescription>
          </div>
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-64 w-full rounded-lg" />
        ) : chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No meeting data available for this period.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip />
              <Bar
                dataKey="count"
                fill="#0f766e"
                radius={[4, 4, 0, 0]}
                name="Meetings"
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

function TopicsTab() {
  const { data: topics, isLoading } = useQuery<TopicFrequency[]>({
    queryKey: ["analytics", "topics"],
    queryFn: getTopicFrequency,
  });

  if (isLoading) {
    return <ChartSkeleton />;
  }

  const chartData = (topics ?? []).map((item) => ({
    name: item.topic,
    value: item.count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Meeting Topics</CardTitle>
        <CardDescription>
          Most discussed topics across your meetings.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              No topic data available yet.
            </p>
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row items-center gap-8">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) =>
                    `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                  }
                  labelLine={true}
                >
                  {chartData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={TEAL_PALETTE[index % TEAL_PALETTE.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name) => [
                    `${value} mentions`,
                    name,
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground mt-1">
          Insights into your meeting patterns and team collaboration.
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="talk-time">Talk Time</TabsTrigger>
          <TabsTrigger value="frequency">Meeting Frequency</TabsTrigger>
          <TabsTrigger value="topics">Topics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <OverviewTab />
        </TabsContent>

        <TabsContent value="talk-time" className="space-y-4">
          <TalkTimeTab />
        </TabsContent>

        <TabsContent value="frequency" className="space-y-4">
          <FrequencyTab />
        </TabsContent>

        <TabsContent value="topics" className="space-y-4">
          <TopicsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
