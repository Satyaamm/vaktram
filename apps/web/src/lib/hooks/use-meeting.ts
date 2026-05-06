"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMeetings,
  getMeeting,
  getTranscript,
  getSummary,
  startBot,
  stopBot,
  deleteMeeting,
} from "@/lib/api/meetings";
import { ApiError } from "@/lib/api/client";
import type { Meeting } from "@/types";

export function useMeetings(filters?: {
  status?: string;
  page?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["meetings", filters],
    queryFn: async (): Promise<Meeting[]> => {
      const result = await getMeetings(filters);
      return result.items;
    },
  });
}

export function useMeeting(id: string) {
  return useQuery({
    queryKey: ["meeting", id],
    queryFn: () => getMeeting(id),
    enabled: !!id,
  });
}

// Transcript and summary 404s are *expected* whenever a meeting hasn't
// finished its pipeline yet. We treat 404 as "no data yet" rather than
// an error — return null so the page renders the friendly placeholder
// ("Summary will appear once processing completes") instead of toasting
// or hiding behind a generic error state. retry: false keeps Tanstack
// from re-querying a known 404.
function nullOn404<T>(loader: () => Promise<T>) {
  return async (): Promise<T | null> => {
    try {
      return await loader();
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return null;
      throw e;
    }
  };
}

export function useTranscript(meetingId: string) {
  return useQuery({
    queryKey: ["transcript", meetingId],
    queryFn: nullOn404(() => getTranscript(meetingId)),
    enabled: !!meetingId,
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status === 404) && failureCount < 2,
  });
}

export function useSummary(meetingId: string) {
  return useQuery({
    queryKey: ["summary", meetingId],
    queryFn: nullOn404(() => getSummary(meetingId)),
    enabled: !!meetingId,
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status === 404) && failureCount < 2,
  });
}

export function useStartBot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ meetingId, meetingUrl }: { meetingId: string; meetingUrl: string }) =>
      startBot(meetingId, meetingUrl),
    onSuccess: (_data, { meetingId }) => {
      queryClient.invalidateQueries({ queryKey: ["meeting", meetingId] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
  });
}

export function useStopBot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (meetingId: string) => stopBot(meetingId),
    onSuccess: (_data, meetingId) => {
      queryClient.invalidateQueries({ queryKey: ["meeting", meetingId] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
  });
}

export function useDeleteMeeting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (meetingId: string) => deleteMeeting(meetingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
  });
}
