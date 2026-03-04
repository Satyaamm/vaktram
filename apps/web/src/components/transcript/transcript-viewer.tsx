"use client";

import { useEffect, useRef } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { TranscriptSegment } from "@/types";

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  currentTime?: number;
  onTimestampClick: (time: number) => void;
}

export function TranscriptViewer({
  segments,
  currentTime = 0,
  onTimestampClick,
}: TranscriptViewerProps) {
  const activeRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeIndex = segments.findIndex(
    (seg, i) =>
      currentTime >= seg.start_time &&
      (i === segments.length - 1 || currentTime < segments[i + 1].start_time)
  );

  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      activeRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [activeIndex]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transcript</CardTitle>
        <CardDescription>
          Full meeting transcript with speaker labels. Click a timestamp to jump
          to that point in the audio.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          ref={containerRef}
          className="space-y-1 max-h-[600px] overflow-y-auto pr-2"
        >
          {segments.map((segment, i) => {
            const isActive = i === activeIndex;

            return (
              <div
                key={segment.id}
                ref={isActive ? activeRef : undefined}
                className={`flex gap-3 rounded-lg p-3 transition-colors ${
                  isActive ? "bg-teal-50 dark:bg-teal-950/30" : ""
                }`}
              >
                <Avatar className="h-8 w-8 mt-0.5 shrink-0">
                  <AvatarFallback className="bg-teal-700 text-white text-xs">
                    {getInitials(segment.speaker_name)}
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-teal-700 dark:text-teal-400">
                      {segment.speaker_name}
                    </span>
                    <button
                      onClick={() => onTimestampClick(segment.start_time)}
                      className="text-xs text-slate-500 hover:text-teal-700 dark:hover:text-teal-400 transition-colors cursor-pointer tabular-nums"
                    >
                      {formatTime(segment.start_time)}
                    </button>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {segment.content}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
