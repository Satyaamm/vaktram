"use client";

import { useRef, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import {
  Share2,
  Download,
  Video,
  Monitor,
  Users as UsersIcon,
  Globe,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AudioPlayer,
  type AudioPlayerHandle,
} from "@/components/audio-player/audio-player";
import { TranscriptViewer } from "@/components/transcript/transcript-viewer";
import { MeetingSummary } from "@/components/meetings/meeting-summary";
import { useMeeting, useTranscript, useSummary } from "@/lib/hooks/use-meeting";
import {
  CheckCircle2,
  Circle,
  Clock,
} from "lucide-react";

const platformIcons: Record<string, React.ElementType> = {
  zoom: Video,
  google_meet: Monitor,
  teams: UsersIcon,
  other: Globe,
};

const platformLabels: Record<string, string> = {
  zoom: "Zoom",
  google_meet: "Google Meet",
  teams: "Microsoft Teams",
  other: "Other",
};

const statusColors: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  in_progress:
    "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  completed: "bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300",
  cancelled: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};

const priorityConfig = {
  high: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  low: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
};

const statusIcons = {
  pending: Circle,
  in_progress: Clock,
  completed: CheckCircle2,
};

function formatDuration(seconds: number | null): string {
  if (!seconds) return "N/A";
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins} min`;
}

function MeetingDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-9 w-80" />
          <Skeleton className="h-5 w-60" />
          <div className="flex gap-2 mt-2">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-6 w-32" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
        </div>
      </div>
      <Skeleton className="h-20 w-full rounded-xl" />
      <div className="space-y-4">
        <Skeleton className="h-10 w-80" />
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    </div>
  );
}

export default function MeetingDetailPage() {
  const params = useParams<{ id: string }>();
  const meetingId = params.id;

  const audioPlayerRef = useRef<AudioPlayerHandle>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const {
    data: meeting,
    isLoading: meetingLoading,
    error: meetingError,
  } = useMeeting(meetingId);

  const {
    data: transcript,
    isLoading: transcriptLoading,
  } = useTranscript(meetingId);

  const {
    data: summary,
    isLoading: summaryLoading,
  } = useSummary(meetingId);

  const handleTimestampClick = useCallback((time: number) => {
    audioPlayerRef.current?.seekTo(time);
  }, []);

  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
  }, []);

  if (meetingLoading) {
    return <MeetingDetailSkeleton />;
  }

  if (meetingError || !meeting) {
    return (
      <Alert variant="destructive" className="max-w-2xl mx-auto mt-8">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error loading meeting</AlertTitle>
        <AlertDescription>
          {meetingError instanceof Error
            ? meetingError.message
            : "The meeting could not be found. Please check the URL and try again."}
        </AlertDescription>
      </Alert>
    );
  }

  const PlatformIcon = platformIcons[meeting.platform] || Globe;

  return (
    <div className="space-y-6">
      {/* Meeting Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">
            {meeting.title}
          </h1>
          <p className="text-muted-foreground">
            {meeting.started_at
              ? format(new Date(meeting.started_at), "MMM d, yyyy · h:mm a")
              : format(new Date(meeting.created_at), "MMM d, yyyy")}
            {meeting.duration_seconds
              ? ` · ${formatDuration(meeting.duration_seconds)}`
              : ""}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary" className={statusColors[meeting.status]}>
              {meeting.status.replace("_", " ")}
            </Badge>
            <Badge variant="outline" className="gap-1">
              <PlatformIcon className="h-3 w-3" />
              {platformLabels[meeting.platform]}
            </Badge>
            <Badge variant="outline">
              {meeting.participant_count} participant
              {meeting.participant_count !== 1 ? "s" : ""}
            </Badge>
          </div>
          {meeting.description && (
            <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
              {meeting.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Share2 className="mr-2 h-4 w-4" />
            Share
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Audio Player */}
      {meeting.recording_url ? (
        <AudioPlayer
          ref={audioPlayerRef}
          audioUrl={meeting.recording_url}
          onTimeUpdate={handleTimeUpdate}
        />
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center h-12 rounded-lg bg-muted">
              <p className="text-sm text-muted-foreground">
                No audio recording available for this meeting.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs defaultValue="transcript" className="space-y-4">
        <TabsList>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="action-items">
            Action Items
            {summary && summary.action_items.length > 0 && (
              <Badge
                variant="secondary"
                className="ml-2 h-5 px-1.5 text-xs bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300"
              >
                {summary.action_items.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Transcript Tab */}
        <TabsContent value="transcript">
          {transcriptLoading ? (
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-64 mt-1" />
              </CardHeader>
              <CardContent className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex gap-3">
                    <Skeleton className="h-8 w-8 rounded-full shrink-0" />
                    <div className="space-y-2 flex-1">
                      <Skeleton className="h-4 w-40" />
                      <Skeleton className="h-4 w-full" />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : transcript && transcript.length > 0 ? (
            <TranscriptViewer
              segments={transcript}
              currentTime={currentTime}
              onTimestampClick={handleTimestampClick}
            />
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    No transcript available yet.
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Transcripts are generated after the meeting ends.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Summary Tab */}
        <TabsContent value="summary">
          {summaryLoading ? (
            <div className="space-y-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-20 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : summary ? (
            <MeetingSummary summary={summary} />
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    No summary available yet.
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Summaries are generated after the transcript is processed.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Action Items Tab */}
        <TabsContent value="action-items">
          {summaryLoading ? (
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-48 mt-1" />
              </CardHeader>
              <CardContent className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-lg" />
                ))}
              </CardContent>
            </Card>
          ) : summary && summary.action_items.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Action Items</CardTitle>
                <CardDescription>
                  {summary.action_items.length} task
                  {summary.action_items.length !== 1 ? "s" : ""} extracted from
                  this meeting.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {summary.action_items.map((item) => {
                    const StatusIcon = statusIcons[item.status];

                    return (
                      <div
                        key={item.id}
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
                            <p className="text-xs text-muted-foreground">
                              {item.assignee_name &&
                                `Assigned to ${item.assignee_name}`}
                              {item.assignee_name && item.due_date && " · "}
                              {item.due_date && `Due ${item.due_date}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="secondary"
                            className={priorityConfig[item.priority]}
                          >
                            {item.priority}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={
                              item.status === "in_progress"
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                                : item.status === "completed"
                                ? "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300"
                                : ""
                            }
                          >
                            {item.status.replace("_", " ")}
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    No action items found.
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Action items are extracted from the meeting summary.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
