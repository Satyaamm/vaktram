import { create } from "zustand";
import type { Meeting } from "@/types";

interface MeetingFilters {
  status: string | null;
  platform: string | null;
  dateRange: { from: string | null; to: string | null };
  search: string;
}

interface MeetingState {
  meetings: Meeting[];
  selectedMeeting: Meeting | null;
  isRecording: boolean;
  isLoading: boolean;
  filters: MeetingFilters;
  setMeetings: (meetings: Meeting[]) => void;
  setSelectedMeeting: (meeting: Meeting | null) => void;
  setIsRecording: (isRecording: boolean) => void;
  setIsLoading: (isLoading: boolean) => void;
  setFilters: (filters: Partial<MeetingFilters>) => void;
  resetFilters: () => void;
}

const defaultFilters: MeetingFilters = {
  status: null,
  platform: null,
  dateRange: { from: null, to: null },
  search: "",
};

export const useMeetingStore = create<MeetingState>((set) => ({
  meetings: [],
  selectedMeeting: null,
  isRecording: false,
  isLoading: false,
  filters: defaultFilters,
  setMeetings: (meetings) => set({ meetings }),
  setSelectedMeeting: (selectedMeeting) => set({ selectedMeeting }),
  setIsRecording: (isRecording) => set({ isRecording }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),
  resetFilters: () => set({ filters: defaultFilters }),
}));
