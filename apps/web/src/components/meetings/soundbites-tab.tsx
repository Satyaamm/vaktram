"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Scissors,
  Copy,
  Check,
  Share2,
  Loader2,
  Volume2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { soundbitesApi, type Soundbite } from "@/lib/api/soundbites";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const APP_BASE = process.env.NEXT_PUBLIC_APP_URL || "";

function formatTimestamp(s: number): string {
  const sec = Math.max(0, Math.floor(s));
  const m = Math.floor(sec / 60);
  const r = sec % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
}

function parseTimestamp(value: string): number {
  // Accept "12", "1:23", "1:23.5", "01:23"
  const trimmed = value.trim();
  if (!trimmed) return 0;
  if (!trimmed.includes(":")) return Number(trimmed) || 0;
  const [m, s] = trimmed.split(":");
  return (Number(m) || 0) * 60 + (Number(s) || 0);
}

export function SoundbitesTab({
  meetingId,
  duration,
  currentTime,
  onSeek,
}: {
  meetingId: string;
  duration?: number | null;
  currentTime?: number;
  onSeek?: (seconds: number) => void;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [start, setStart] = useState("0:00");
  const [end, setEnd] = useState("0:30");
  const [title, setTitle] = useState("");
  const [transcript, setTranscript] = useState("");
  const [copied, setCopied] = useState<string | null>(null);
  const lastUseTime = useRef(currentTime ?? 0);
  lastUseTime.current = currentTime ?? lastUseTime.current;

  const { data: soundbites, isLoading } = useQuery({
    queryKey: ["soundbites", meetingId],
    queryFn: () => soundbitesApi.forMeeting(meetingId),
  });

  const create = useMutation({
    mutationFn: (body: {
      start_seconds: number;
      end_seconds: number;
      title?: string;
      transcript?: string;
    }) =>
      soundbitesApi.create({
        meeting_id: meetingId,
        ...body,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["soundbites", meetingId] });
      setTitle("");
      setTranscript("");
      toast({ title: "Soundbite created", description: "Share link copied below." });
    },
    onError: (e: Error) => {
      toast({
        title: "Couldn't create soundbite",
        description: e.message,
        variant: "destructive",
      });
    },
  });

  const startSec = parseTimestamp(start);
  const endSec = parseTimestamp(end);
  const valid = endSec > startSec && endSec - startSec <= 600;

  const useCurrentForStart = () => {
    setStart(formatTimestamp(lastUseTime.current));
  };
  const useCurrentForEnd = () => {
    setEnd(formatTimestamp(lastUseTime.current));
  };

  const handleCopy = async (token: string) => {
    const base = APP_BASE || (typeof window !== "undefined" ? window.location.origin : "");
    const url = `${base}/s/${token}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(token);
      setTimeout(() => setCopied(null), 1800);
    } catch {
      toast({ title: "Copy failed", description: url });
    }
  };

  const submit = () => {
    if (!valid) return;
    create.mutate({
      start_seconds: startSec,
      end_seconds: endSec,
      title: title.trim() || undefined,
      transcript: transcript.trim() || undefined,
    });
  };

  const durationLabel = useMemo(
    () => (duration ? `Meeting length ${formatTimestamp(duration)}` : "Time format mm:ss or seconds"),
    [duration],
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Scissors className="h-5 w-5 text-teal-700" />
            Create soundbite
          </CardTitle>
          <CardDescription>{durationLabel}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <Label htmlFor="sb-start" className="text-xs">Start</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="sb-start"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                  placeholder="1:23"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={useCurrentForStart}
                  title="Use current playback time"
                >
                  Now
                </Button>
              </div>
            </div>
            <div>
              <Label htmlFor="sb-end" className="text-xs">End</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="sb-end"
                  value={end}
                  onChange={(e) => setEnd(e.target.value)}
                  placeholder="1:53"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={useCurrentForEnd}
                  title="Use current playback time"
                >
                  Now
                </Button>
              </div>
            </div>
          </div>

          <div>
            <Label htmlFor="sb-title" className="text-xs">Title (optional)</Label>
            <Input
              id="sb-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Pricing objection — Acme call"
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="sb-transcript" className="text-xs">Transcript (optional)</Label>
            <Input
              id="sb-transcript"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Quote shown on the share page"
              className="mt-1"
            />
          </div>

          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Selected range:{" "}
              <span className="font-mono">
                {formatTimestamp(startSec)} → {formatTimestamp(endSec)}
              </span>{" "}
              ({Math.max(0, endSec - startSec).toFixed(0)}s)
              {!valid && (
                <span className="ml-2 text-red-600">
                  end must be after start, max 10 min
                </span>
              )}
            </p>
            <Button
              onClick={submit}
              disabled={!valid || create.isPending}
              className="bg-teal-700 hover:bg-teal-800 text-white"
            >
              {create.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
              Create soundbite
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="h-5 w-5 text-teal-700" />
            Saved soundbites
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !soundbites || soundbites.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No soundbites yet. Pick a moment with the audio player and create one above.
            </p>
          ) : (
            <ul className="space-y-2">
              {soundbites.map((sb) => (
                <SoundbiteRow
                  key={sb.id}
                  sb={sb}
                  copied={copied}
                  onCopy={handleCopy}
                  onSeek={onSeek}
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SoundbiteRow({
  sb,
  copied,
  onCopy,
  onSeek,
}: {
  sb: Soundbite;
  copied: string | null;
  onCopy: (token: string) => void;
  onSeek?: (seconds: number) => void;
}) {
  // share_url comes back like "/s/<token>" — extract the token.
  const token = sb.share_url?.split("/").pop() ?? null;
  const isCopied = copied === token;

  return (
    <li className="flex items-center justify-between gap-3 rounded-md border p-3">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium truncate">
          {sb.title || `Clip ${formatTimestamp(sb.start)}`}
        </p>
        <p className="text-xs text-muted-foreground font-mono">
          {formatTimestamp(sb.start)} → {formatTimestamp(sb.end)} ({(sb.end - sb.start).toFixed(0)}s)
        </p>
        {sb.transcript && (
          <p className="text-xs text-muted-foreground italic line-clamp-1 mt-0.5">
            “{sb.transcript}”
          </p>
        )}
      </div>
      <div className="flex items-center gap-1 shrink-0">
        {onSeek && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onSeek(sb.start)}
            title="Jump to start in player"
          >
            ▶
          </Button>
        )}
        {token && (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCopy(token)}
              title="Copy share link"
            >
              {isCopied ? (
                <Check className="h-3.5 w-3.5 text-green-600" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
            <a
              href={`/s/${token}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center h-9 px-3 rounded-md border text-sm hover:bg-muted"
              title="Open share page"
            >
              <Share2 className="h-3.5 w-3.5" />
            </a>
          </>
        )}
      </div>
    </li>
  );
}
