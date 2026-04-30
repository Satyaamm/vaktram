"use client";

import {
  useEffect,
  useRef,
  useState,
  useCallback,
  useImperativeHandle,
  forwardRef,
} from "react";
import WaveSurfer from "wavesurfer.js";
import { Play, Pause, Volume2, VolumeX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export interface AudioPlayerHandle {
  seekTo: (time: number) => void;
}

interface AudioPlayerProps {
  audioUrl: string;
  onTimeUpdate?: (time: number) => void;
}

export const AudioPlayer = forwardRef<AudioPlayerHandle, AudioPlayerProps>(
  function AudioPlayer({ audioUrl, onTimeUpdate }, ref) {
    const waveformRef = useRef<HTMLDivElement>(null);
    const wavesurferRef = useRef<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [playbackRate, setPlaybackRate] = useState("1");
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isReady, setIsReady] = useState(false);

    useImperativeHandle(ref, () => ({
      seekTo: (time: number) => {
        const ws = wavesurferRef.current;
        if (ws && duration > 0) {
          ws.seekTo(time / duration);
        }
      },
    }));

    useEffect(() => {
      if (!waveformRef.current) return;

      const ws = WaveSurfer.create({
        container: waveformRef.current,
        waveColor: "#CBD5E1",
        progressColor: "#0F766E",
        cursorColor: "#0F766E",
        barWidth: 2,
        barGap: 1,
        barRadius: 2,
        height: 48,
        normalize: true,
      });

      ws.load(audioUrl);

      ws.on("ready", () => {
        setDuration(ws.getDuration());
        setIsReady(true);
      });

      ws.on("audioprocess", () => {
        const time = ws.getCurrentTime();
        setCurrentTime(time);
        onTimeUpdate?.(time);
      });

      ws.on("seeking", () => {
        const time = ws.getCurrentTime();
        setCurrentTime(time);
        onTimeUpdate?.(time);
      });

      ws.on("play", () => setIsPlaying(true));
      ws.on("pause", () => setIsPlaying(false));
      ws.on("finish", () => setIsPlaying(false));

      wavesurferRef.current = ws;

      return () => {
        try {
          ws.destroy();
        } catch {
          // Ignore abort errors during cleanup
        }
        wavesurferRef.current = null;
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [audioUrl]);

    const togglePlayPause = useCallback(() => {
      wavesurferRef.current?.playPause();
    }, []);

    const handlePlaybackRateChange = useCallback((rate: string) => {
      setPlaybackRate(rate);
      wavesurferRef.current?.setPlaybackRate(parseFloat(rate));
    }, []);

    const toggleMute = useCallback(() => {
      const ws = wavesurferRef.current;
      if (!ws) return;

      if (isMuted) {
        ws.setVolume(volume);
        setIsMuted(false);
      } else {
        ws.setVolume(0);
        setIsMuted(true);
      }
    }, [isMuted, volume]);

    const handleVolumeChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVolume = parseFloat(e.target.value);
        setVolume(newVolume);
        setIsMuted(newVolume === 0);
        wavesurferRef.current?.setVolume(newVolume);
      },
      []
    );

    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Button
              size="icon"
              onClick={togglePlayPause}
              disabled={!isReady}
              className="h-10 w-10 shrink-0 rounded-full bg-teal-700 hover:bg-teal-800 text-white"
            >
              {isPlaying ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4 ml-0.5" />
              )}
            </Button>

            <div ref={waveformRef} className="flex-1 min-w-0" />

            <span className="text-sm text-muted-foreground whitespace-nowrap tabular-nums">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>

            <Select
              value={playbackRate}
              onValueChange={handlePlaybackRateChange}
            >
              <SelectTrigger className="w-[72px] h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.5">0.5x</SelectItem>
                <SelectItem value="1">1x</SelectItem>
                <SelectItem value="1.5">1.5x</SelectItem>
                <SelectItem value="2">2x</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={toggleMute}
              >
                {isMuted || volume === 0 ? (
                  <VolumeX className="h-4 w-4" />
                ) : (
                  <Volume2 className="h-4 w-4" />
                )}
              </Button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="w-16 h-1 accent-teal-700 cursor-pointer"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
);
