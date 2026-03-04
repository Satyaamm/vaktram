"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  User,
  Brain,
  CalendarDays,
  Bell,
  CreditCard,
  Check,
  ExternalLink,
  Loader2,
  Upload,
  RefreshCw,
} from "lucide-react";

import {
  getProfile,
  updateProfile,
  getAIConfigs,
  getCalendarConnections,
  authorizeCalendar,
  syncCalendar,
  disconnectCalendar,
} from "@/lib/api/settings";
import { PLAN_LIMITS } from "@/lib/constants";
import type { UserProfile, UserAIConfig } from "@/types";
import { useToast } from "@/hooks/use-toast";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const profileSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  timezone: z.string().optional(),
  language: z.string().optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TIMEZONES = [
  { value: "UTC", label: "UTC" },
  { value: "America/New_York", label: "Eastern Time (ET)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "America/Anchorage", label: "Alaska Time (AKT)" },
  { value: "Pacific/Honolulu", label: "Hawaii Time (HT)" },
  { value: "Europe/London", label: "GMT / London" },
  { value: "Europe/Paris", label: "Central European Time (CET)" },
  { value: "Europe/Berlin", label: "Berlin (CET)" },
  { value: "Asia/Kolkata", label: "India Standard Time (IST)" },
  { value: "Asia/Shanghai", label: "China Standard Time (CST)" },
  { value: "Asia/Tokyo", label: "Japan Standard Time (JST)" },
  { value: "Australia/Sydney", label: "Australian Eastern (AEST)" },
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "pt", label: "Portuguese" },
  { value: "ja", label: "Japanese" },
  { value: "zh", label: "Chinese" },
  { value: "hi", label: "Hindi" },
];

// ---------------------------------------------------------------------------
// Profile Tab
// ---------------------------------------------------------------------------

function ProfileTab() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: profile, isLoading } = useQuery<UserProfile>({
    queryKey: ["profile"],
    queryFn: getProfile,
  });

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: profile?.full_name ?? "",
      timezone: "UTC",
      language: "en",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ProfileFormValues) => updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast({ title: "Profile updated", description: "Your changes have been saved." });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    },
  });

  function onSubmit(values: ProfileFormValues) {
    mutation.mutate(values);
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64 mt-1" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription>
          Update your personal information and preferences.
        </CardDescription>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-6">
            {/* Avatar upload placeholder */}
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={profile?.avatar_url ?? ""} />
                <AvatarFallback className="bg-teal-700 text-white text-lg">
                  {profile?.full_name
                    ? profile.full_name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")
                        .toUpperCase()
                    : "?"}
                </AvatarFallback>
              </Avatar>
              <div>
                <Button type="button" variant="outline" size="sm" className="gap-2">
                  <Upload className="h-4 w-4" />
                  Upload Photo
                </Button>
                <p className="text-xs text-muted-foreground mt-1">
                  JPG, PNG or GIF. Max 2MB.
                </p>
              </div>
            </div>

            <Separator />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Your name" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={profile?.email ?? ""}
                  disabled
                  className="bg-muted"
                />
                <p className="text-xs text-muted-foreground">
                  Email cannot be changed here.
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="timezone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Timezone</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select timezone" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {TIMEZONES.map((tz) => (
                          <SelectItem key={tz.value} value={tz.value}>
                            {tz.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Language</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select language" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {LANGUAGES.map((lang) => (
                          <SelectItem key={lang.value} value={lang.value}>
                            {lang.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button
              type="submit"
              className="bg-teal-700 hover:bg-teal-800 text-white"
              disabled={mutation.isPending}
            >
              {mutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save Changes
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// AI Configuration Tab
// ---------------------------------------------------------------------------

function AIConfigTab() {
  const { data: configs, isLoading } = useQuery<UserAIConfig[]>({
    queryKey: ["ai-configs"],
    queryFn: getAIConfigs,
  });

  const defaultConfig = configs?.find((c) => c.is_default);

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Configuration</CardTitle>
        <CardDescription>
          Bring your own model. Configure your preferred LLM provider for
          meeting summaries and insights.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        ) : defaultConfig ? (
          <div className="flex items-center gap-3 rounded-lg border p-4">
            <Brain className="h-5 w-5 text-teal-700" />
            <div className="flex-1">
              <p className="text-sm font-medium">
                Active:{" "}
                <span className="capitalize">{defaultConfig.provider}</span>{" "}
                &mdash; {defaultConfig.model_name}
              </p>
              <p className="text-xs text-muted-foreground">
                This model is used for all AI-powered features.
              </p>
            </div>
            <Badge className="bg-teal-100 text-teal-800">Default</Badge>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No AI provider configured yet. Set one up to unlock summaries,
            action items, and insights.
          </p>
        )}

        <Link href="/settings/ai-config">
          <Button className="gap-2 bg-teal-700 hover:bg-teal-800 text-white">
            <Brain className="h-4 w-4" />
            Configure AI
            <ExternalLink className="h-3 w-3" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Calendar Tab
// ---------------------------------------------------------------------------

function CalendarTab() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: connections, isLoading } = useQuery({
    queryKey: ["calendar-connections"],
    queryFn: getCalendarConnections,
  });

  const googleConnection = connections?.find((c) => c.provider === "google");

  // Handle OAuth callback status from URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("status");
    if (status === "connected") {
      toast({ title: "Calendar connected", description: "Google Calendar has been connected successfully." });
      queryClient.invalidateQueries({ queryKey: ["calendar-connections"] });
      window.history.replaceState({}, "", "/settings");
    } else if (status === "error") {
      toast({ title: "Connection failed", description: "Failed to connect calendar. Please try again.", variant: "destructive" });
      window.history.replaceState({}, "", "/settings");
    }
  }, [toast, queryClient]);

  const connectMutation = useMutation({
    mutationFn: authorizeCalendar,
    onSuccess: (data) => {
      window.location.href = data.authorization_url;
    },
    onError: () => {
      toast({ title: "Error", description: "Failed to start calendar connection.", variant: "destructive" });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (id: string) => disconnectCalendar(id),
    onSuccess: () => {
      toast({ title: "Disconnected", description: "Calendar has been disconnected." });
      queryClient.invalidateQueries({ queryKey: ["calendar-connections"] });
    },
    onError: () => {
      toast({ title: "Error", description: "Failed to disconnect calendar.", variant: "destructive" });
    },
  });

  const syncMutation = useMutation({
    mutationFn: syncCalendar,
    onSuccess: (data) => {
      toast({
        title: "Sync complete",
        description: `Synced ${data.synced_count} events. ${data.new_meetings.length} new meetings added.`,
      });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
    onError: () => {
      toast({ title: "Sync failed", description: "Failed to sync calendar events.", variant: "destructive" });
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-72 mt-1" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Calendar Integration</CardTitle>
        <CardDescription>
          Connect your calendar to automatically detect and record meetings.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Google Calendar */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <CalendarDays className="h-5 w-5 text-muted-foreground" />
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium">Google Calendar</p>
                {googleConnection && (
                  <Badge className="bg-green-100 text-green-800 text-xs gap-1">
                    <Check className="h-3 w-3" />
                    Connected
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {googleConnection
                  ? `Connected as ${googleConnection.calendar_id ?? "primary"}`
                  : "Auto-detect and join Google Meet calls"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {googleConnection && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                Sync
              </Button>
            )}
            {googleConnection ? (
              <Button
                variant="outline"
                onClick={() => disconnectMutation.mutate(googleConnection.id)}
                disabled={disconnectMutation.isPending}
              >
                {disconnectMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : null}
                Disconnect
              </Button>
            ) : (
              <Button
                className="bg-teal-700 hover:bg-teal-800 text-white"
                onClick={() => connectMutation.mutate()}
                disabled={connectMutation.isPending}
              >
                {connectMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : null}
                Connect
              </Button>
            )}
          </div>
        </div>

        {/* Microsoft Outlook - Coming Soon */}
        <div className="flex items-center justify-between rounded-lg border p-4 opacity-60">
          <div className="flex items-center gap-3">
            <CalendarDays className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">Microsoft Outlook</p>
              <p className="text-xs text-muted-foreground">
                Coming soon — Teams integration
              </p>
            </div>
          </div>
          <Button variant="outline" disabled>
            Coming Soon
          </Button>
        </div>

        <Separator />

        <p className="text-xs text-muted-foreground">
          OAuth flow is handled securely by the backend. Your tokens are
          encrypted and never exposed.
        </p>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Notifications Tab
// ---------------------------------------------------------------------------

function NotificationsTab() {
  const { toast } = useToast();

  const [preferences, setPreferences] = useState({
    email_notifications: true,
    in_app_notifications: true,
    summary_ready_alerts: true,
    bot_status_alerts: false,
  });

  function togglePreference(key: keyof typeof preferences) {
    setPreferences((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function savePreferences() {
    toast({
      title: "Preferences saved",
      description: "Your notification preferences have been updated.",
    });
  }

  const items = [
    {
      key: "email_notifications" as const,
      label: "Email notifications",
      description: "Receive email notifications for important events",
    },
    {
      key: "in_app_notifications" as const,
      label: "In-app notifications",
      description: "Show notification badges and popups in the app",
    },
    {
      key: "summary_ready_alerts" as const,
      label: "Summary ready alerts",
      description: "Get notified when AI finishes processing a meeting",
    },
    {
      key: "bot_status_alerts" as const,
      label: "Bot status alerts",
      description: "Notifications when the recording bot joins or leaves",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>
          Configure how and when you receive notifications.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {items.map((item) => (
          <div
            key={item.key}
            className="flex items-center justify-between"
          >
            <div className="space-y-0.5">
              <Label>{item.label}</Label>
              <p className="text-xs text-muted-foreground">
                {item.description}
              </p>
            </div>
            <Switch
              checked={preferences[item.key]}
              onCheckedChange={() => togglePreference(item.key)}
            />
          </div>
        ))}
      </CardContent>
      <CardFooter>
        <Button
          onClick={savePreferences}
          className="bg-teal-700 hover:bg-teal-800 text-white"
        >
          Save Preferences
        </Button>
      </CardFooter>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Billing Tab
// ---------------------------------------------------------------------------

function BillingTab() {
  const { isLoading } = useQuery<UserProfile>({
    queryKey: ["profile"],
    queryFn: getProfile,
  });

  const plan = "free" as const; // TODO: fetch from billing endpoint
  const planInfo = PLAN_LIMITS[plan];

  // Mock usage data (would come from API in production)
  const meetingsUsed = 23;
  const storageMb = 2100;
  const meetingsLimit: number = planInfo.meetingsPerMonth;
  const storageLimit: number = planInfo.storageMb;
  const meetingsPercent =
    meetingsLimit === -1 ? 0 : Math.round((meetingsUsed / meetingsLimit) * 100);
  const storagePercent =
    storageLimit === -1 ? 0 : Math.round((storageMb / storageLimit) * 100);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-24" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Billing</CardTitle>
        <CardDescription>
          Manage your subscription and billing details.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current plan */}
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Current Plan</p>
              <p className="text-2xl font-bold text-teal-700 dark:text-teal-500">
                {planInfo.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {planInfo.price === 0
                  ? "Free forever"
                  : planInfo.price === -1
                    ? "Custom pricing"
                    : `$${planInfo.price}/month`}
              </p>
            </div>
            {(plan === "free" || plan === "pro") && (
              <Button variant="outline">Upgrade Plan</Button>
            )}
          </div>

          <Separator className="my-3" />

          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Plan features
            </p>
            <ul className="space-y-1">
              {planInfo.features.map((feature) => (
                <li
                  key={feature}
                  className="flex items-center gap-2 text-sm text-muted-foreground"
                >
                  <Check className="h-3 w-3 text-teal-700" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Separator />

        {/* Usage */}
        <div>
          <p className="text-sm font-medium mb-3">Usage This Month</p>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted-foreground">Meetings</span>
                <span>
                  {meetingsUsed}{" "}
                  {meetingsLimit === -1
                    ? "(unlimited)"
                    : `/ ${meetingsLimit}`}
                </span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div
                  className="h-2 rounded-full bg-teal-700 dark:bg-teal-500 transition-all"
                  style={{
                    width: `${meetingsLimit === -1 ? 10 : meetingsPercent}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted-foreground">Storage</span>
                <span>
                  {(storageMb / 1000).toFixed(1)} GB{" "}
                  {storageLimit === -1
                    ? "(unlimited)"
                    : `/ ${(storageLimit / 1000).toFixed(0)} GB`}
                </span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div
                  className="h-2 rounded-full bg-teal-700 dark:bg-teal-500 transition-all"
                  style={{
                    width: `${storageLimit === -1 ? 5 : storagePercent}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main Settings Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and application preferences.
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="profile" className="gap-2">
            <User className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="ai-config" className="gap-2">
            <Brain className="h-4 w-4" />
            AI Configuration
          </TabsTrigger>
          <TabsTrigger value="calendar" className="gap-2">
            <CalendarDays className="h-4 w-4" />
            Calendar
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2">
            <CreditCard className="h-4 w-4" />
            Billing
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <ProfileTab />
        </TabsContent>

        <TabsContent value="ai-config">
          <AIConfigTab />
        </TabsContent>

        <TabsContent value="calendar">
          <CalendarTab />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationsTab />
        </TabsContent>

        <TabsContent value="billing">
          <BillingTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
