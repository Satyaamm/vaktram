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

export function useMeetings(filters?: {
  status?: string;
  page?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["meetings", filters],
    queryFn: () => getMeetings(filters),
  });
}

export function useMeeting(id: string) {
  return useQuery({
    queryKey: ["meeting", id],
    queryFn: () => getMeeting(id),
    enabled: !!id,
  });
}

export function useTranscript(meetingId: string) {
  return useQuery({
    queryKey: ["transcript", meetingId],
    queryFn: () => getTranscript(meetingId),
    enabled: !!meetingId,
  });
}

export function useSummary(meetingId: string) {
  return useQuery({
    queryKey: ["summary", meetingId],
    queryFn: () => getSummary(meetingId),
    enabled: !!meetingId,
  });
}

export function useStartBot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (meetingId: string) => startBot(meetingId),
    onSuccess: (_data, meetingId) => {
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
