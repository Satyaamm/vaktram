"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Plus,
  Video,
  Monitor,
  Users as UsersIcon,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Loader2,
} from "lucide-react";
import { useMeetings } from "@/lib/hooks/use-meeting";
import { createMeeting } from "@/lib/api/meetings";
import type { Meeting, CreateMeetingInput } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Skeleton } from "@/components/ui/skeleton";

const ITEMS_PER_PAGE = 10;

const createMeetingSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  meeting_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  platform: z.enum(["zoom", "google_meet", "teams", "other"]),
  scheduled_at: z.string().optional().or(z.literal("")),
  description: z.string().optional().or(z.literal("")),
});

type CreateMeetingFormValues = z.infer<typeof createMeetingSchema>;

function formatDuration(seconds: number | null): string {
  if (!seconds) return "--";
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function platformLabel(platform: Meeting["platform"]): string {
  switch (platform) {
    case "zoom":
      return "Zoom";
    case "google_meet":
      return "Google Meet";
    case "teams":
      return "Teams";
    default:
      return "Other";
  }
}

function PlatformIcon({ platform }: { platform: Meeting["platform"] }) {
  switch (platform) {
    case "zoom":
      return <Video className="h-4 w-4 text-blue-600" />;
    case "google_meet":
      return <Monitor className="h-4 w-4 text-green-600" />;
    case "teams":
      return <UsersIcon className="h-4 w-4 text-purple-600" />;
    default:
      return <Video className="h-4 w-4 text-muted-foreground" />;
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

function TableLoadingSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 py-3">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export default function MeetingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [sortDesc, setSortDesc] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const filters = {
    status: statusFilter !== "all" ? statusFilter : undefined,
    page,
    limit: ITEMS_PER_PAGE,
  };

  const { data: meetings, isLoading } = useMeetings(filters);

  // Client-side filtering for search and platform (API only supports status filter)
  const filteredMeetings = (meetings ?? [])
    .filter((m) => {
      if (debouncedSearch) {
        return m.title.toLowerCase().includes(debouncedSearch.toLowerCase());
      }
      return true;
    })
    .filter((m) => {
      if (platformFilter !== "all") {
        return m.platform === platformFilter;
      }
      return true;
    })
    .sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return sortDesc ? dateB - dateA : dateA - dateB;
    });

  // Create meeting mutation
  const createMeetingMutation = useMutation({
    mutationFn: (data: CreateMeetingInput) => createMeeting(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      setDialogOpen(false);
      form.reset();
    },
  });

  const form = useForm<CreateMeetingFormValues>({
    resolver: zodResolver(createMeetingSchema),
    defaultValues: {
      title: "",
      meeting_url: "",
      platform: "zoom",
      scheduled_at: "",
      description: "",
    },
  });

  function onSubmit(values: CreateMeetingFormValues) {
    const payload: CreateMeetingInput = {
      title: values.title,
      platform: values.platform,
    };
    if (values.meeting_url) payload.meeting_url = values.meeting_url;
    if (values.scheduled_at) payload.scheduled_start = values.scheduled_at;
    createMeetingMutation.mutate(payload);
  }

  const hasNextPage = (meetings?.length ?? 0) === ITEMS_PER_PAGE;
  const hasPrevPage = page > 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Meetings</h1>
          <p className="text-muted-foreground mt-1">
            View and manage all your recorded meetings.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-teal-700 hover:bg-teal-800 text-white">
              <Plus className="mr-2 h-4 w-4" />
              New Meeting
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[480px]">
            <DialogHeader>
              <DialogTitle>Create New Meeting</DialogTitle>
              <DialogDescription>
                Set up a new meeting to record and transcribe.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Title</FormLabel>
                      <FormControl>
                        <Input placeholder="Weekly standup" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="platform"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Platform</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select platform" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="zoom">Zoom</SelectItem>
                          <SelectItem value="google_meet">
                            Google Meet
                          </SelectItem>
                          <SelectItem value="teams">Microsoft Teams</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="meeting_url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Meeting URL (optional)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="https://zoom.us/j/123456"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="scheduled_at"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Scheduled Date & Time (optional)</FormLabel>
                      <FormControl>
                        <Input type="datetime-local" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description (optional)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Brief description of the meeting"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="bg-teal-700 hover:bg-teal-800 text-white"
                    disabled={createMeetingMutation.isPending}
                  >
                    {createMeetingMutation.isPending && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Create Meeting
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <Input
              placeholder="Search meetings..."
              className="sm:max-w-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={platformFilter}
              onValueChange={(value) => {
                setPlatformFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Platforms</SelectItem>
                <SelectItem value="google_meet">Google Meet</SelectItem>
                <SelectItem value="zoom">Zoom</SelectItem>
                <SelectItem value="teams">Teams</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Meetings Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Meetings</CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading meetings..."
              : `Showing ${filteredMeetings.length} meeting${filteredMeetings.length !== 1 ? "s" : ""}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <TableLoadingSkeleton />
          ) : filteredMeetings.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Video className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground">
                No meetings found.
              </p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>
                      <button
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={() => setSortDesc(!sortDesc)}
                      >
                        Date
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Platform</TableHead>
                    <TableHead>Participants</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredMeetings.map((meeting) => (
                    <TableRow
                      key={meeting.id}
                      className="cursor-pointer"
                      onClick={() => router.push(`/meetings/${meeting.id}`)}
                    >
                      <TableCell className="font-medium">
                        <Link
                          href={`/meetings/${meeting.id}`}
                          className="text-teal-700 hover:underline dark:text-teal-500"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {meeting.title}
                        </Link>
                      </TableCell>
                      <TableCell>{formatDate(meeting.created_at)}</TableCell>
                      <TableCell>
                        {formatDuration(meeting.duration_seconds)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <PlatformIcon platform={meeting.platform} />
                          <span>{platformLabel(meeting.platform)}</span>
                        </div>
                      </TableCell>
                      <TableCell>{meeting.participants?.length ?? 0}</TableCell>
                      <TableCell>{statusBadge(meeting.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between pt-4">
                <p className="text-sm text-muted-foreground">Page {page}</p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!hasPrevPage}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!hasNextPage}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
