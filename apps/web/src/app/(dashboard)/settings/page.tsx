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
  Shield,
  Archive,
  ArrowUpRight,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";

import { billingApi, type PlanTier } from "@/lib/api/billing";
import { complianceApi } from "@/lib/api/compliance";

import {
  getProfile,
  updateProfile,
  getAIConfigs,
  getCalendarConnections,
  authorizeCalendar,
  syncCalendar,
  disconnectCalendar,
  getUsage,
} from "@/lib/api/settings";
import { PLAN_LIMITS } from "@/lib/constants";
import type { UserProfile, UserAIConfig } from "@/types";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore, type BackendProfile } from "@/lib/stores/auth-store";

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
      timezone: profile?.timezone ?? "UTC",
      language: profile?.language ?? "en",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ProfileFormValues) => updateProfile(data),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      // Sync the auth store so header/sidebar reflect changes immediately
      try {
        const updated = await getProfile();
        useAuthStore.getState().setProfile(updated as unknown as BackendProfile);
      } catch { /* ignore */ }
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
                <Button type="button" variant="outline" size="sm" className="gap-2" disabled>
                  <Upload className="h-4 w-4" />
                  Upload Photo
                </Button>
                <p className="text-xs text-muted-foreground mt-1">
                  Coming soon. JPG, PNG or GIF. Max 2MB.
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
// Billing Tab — real subscription + Stripe checkout/portal
// ---------------------------------------------------------------------------

function formatUsage(kind: string, used: number): string {
  if (kind === "transcription_minutes" || kind === "bot_minutes") {
    const h = Math.floor(used / 60);
    const m = used % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }
  if (kind === "llm_input_tokens" || kind === "llm_output_tokens") {
    if (used >= 1_000_000) return `${(used / 1_000_000).toFixed(1)}M tokens`;
    if (used >= 1_000) return `${(used / 1_000).toFixed(1)}k tokens`;
    return `${used} tokens`;
  }
  return String(used);
}

function humanizeKind(kind: string): string {
  return kind.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function BillingTab() {
  const { toast } = useToast();
  const { data: subscription, isLoading: subLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: billingApi.subscription,
    retry: 1,
  });
  const { data: usage, isLoading: usageLoading } = useQuery({
    queryKey: ["billing-usage"],
    queryFn: billingApi.usage,
    retry: 1,
  });
  const { data: plans } = useQuery({
    queryKey: ["billing-plans"],
    queryFn: billingApi.plans,
  });

  const checkout = useMutation({
    mutationFn: (plan: PlanTier) => {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      return billingApi.checkout({
        plan,
        seats: 1,
        success_url: `${origin}/settings?status=upgraded`,
        cancel_url: `${origin}/settings`,
      });
    },
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
    onError: (e: Error) => {
      toast({
        title: "Checkout unavailable",
        description: e.message || "Stripe is not configured yet.",
        variant: "destructive",
      });
    },
  });

  const portal = useMutation({
    mutationFn: () => {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      return billingApi.portal(`${origin}/settings`);
    },
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
    onError: (e: Error) => {
      toast({
        title: "Portal unavailable",
        description: e.message,
        variant: "destructive",
      });
    },
  });

  if (subLoading || usageLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-24" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  const plan = subscription?.plan ?? "free";
  const planInfo = plans?.[plan];
  const periodEnd = subscription?.current_period_end
    ? new Date(subscription.current_period_end).toLocaleDateString()
    : null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Subscription</CardTitle>
          <CardDescription>
            Manage your plan and billing details. Powered by Stripe.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-medium">Current plan</p>
                <p className="text-2xl font-bold text-teal-700 capitalize">
                  {planInfo?.name ?? plan}
                </p>
                <p className="text-xs text-muted-foreground">
                  {subscription?.status === "trialing" && "Trial · "}
                  {subscription?.seats ?? 1} seat
                  {(subscription?.seats ?? 1) === 1 ? "" : "s"}
                  {periodEnd && ` · renews ${periodEnd}`}
                  {subscription?.cancel_at_period_end && " · cancels at period end"}
                </p>
              </div>
              <div className="flex flex-col gap-2">
                <Button
                  variant="outline"
                  onClick={() => portal.mutate()}
                  disabled={portal.isPending}
                >
                  {portal.isPending && (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  )}
                  Manage subscription
                </Button>
              </div>
            </div>

            {planInfo && (
              <>
                <Separator className="my-3" />
                <ul className="space-y-1">
                  {planInfo.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-center gap-2 text-sm text-muted-foreground"
                    >
                      <Check className="h-3 w-3 text-teal-700" /> {f}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>

          {plan !== "enterprise" && plans && (
            <div className="grid gap-3 md:grid-cols-3">
              {(["pro", "team", "business"] as PlanTier[])
                .filter((t) => t !== plan)
                .map((tier) => {
                  const p = plans[tier];
                  if (!p) return null;
                  return (
                    <Card key={tier} className="p-4">
                      <p className="font-semibold">{p.name}</p>
                      <p className="text-xl font-bold mt-1">
                        ${(p.monthly_price_cents / 100).toFixed(0)}
                        <span className="text-xs font-normal text-muted-foreground">
                          /seat/mo
                        </span>
                      </p>
                      <Button
                        size="sm"
                        className="mt-3 w-full bg-teal-700 hover:bg-teal-800 text-white"
                        onClick={() => checkout.mutate(tier)}
                        disabled={checkout.isPending}
                      >
                        {checkout.isPending && (
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        )}
                        Upgrade <ArrowUpRight className="h-3 w-3 ml-1" />
                      </Button>
                    </Card>
                  );
                })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Usage this period</CardTitle>
          <CardDescription>
            Resets on{" "}
            {usage?.period_start
              ? new Date(usage.period_start).toLocaleDateString()
              : "the 1st"}
            . Live counters from the pipeline.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {usage?.entries.map((e) => {
            const unlimited = e.limit === 0;
            const pct = unlimited
              ? 5
              : Math.min(100, Math.round((e.used / e.limit) * 100));
            return (
              <div key={e.kind}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">
                    {humanizeKind(e.kind)}
                  </span>
                  <span>
                    {formatUsage(e.kind, e.used)}{" "}
                    <span className="text-muted-foreground">
                      {unlimited ? "(unlimited)" : `/ ${formatUsage(e.kind, e.limit)}`}
                    </span>
                  </span>
                </div>
                <div className="h-2 rounded-full bg-muted">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      pct >= 90
                        ? "bg-red-600"
                        : pct >= 75
                          ? "bg-amber-500"
                          : "bg-teal-700"
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Audit Log Tab
// ---------------------------------------------------------------------------

function AuditTab() {
  const { data: rows, isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: () => complianceApi.listAudit(200),
    retry: 1,
  });

  const verify = useMutation({ mutationFn: complianceApi.verifyChain });

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>Audit log</CardTitle>
          <CardDescription>
            Hash-chained, tamper-evident record of every privileged action.
            SOC 2 evidence comes from this.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => verify.mutate()}
          disabled={verify.isPending}
        >
          {verify.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin mr-1" />
          ) : verify.data?.ok === true ? (
            <ShieldCheck className="h-4 w-4 mr-1 text-green-600" />
          ) : verify.data?.ok === false ? (
            <ShieldAlert className="h-4 w-4 mr-1 text-red-600" />
          ) : (
            <Shield className="h-4 w-4 mr-1" />
          )}
          Verify chain
        </Button>
      </CardHeader>
      <CardContent>
        {verify.data && (
          <p className="text-sm mb-3">
            Checked {verify.data.checked} entries —{" "}
            {verify.data.ok ? (
              <span className="text-green-700">chain intact ✓</span>
            ) : (
              <span className="text-red-700">
                {verify.data.breaks.length} break(s): {verify.data.breaks.join(", ")}
              </span>
            )}
          </p>
        )}
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : !rows || rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">No audit entries yet.</p>
        ) : (
          <div className="rounded-md border max-h-[60vh] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 sticky top-0">
                <tr>
                  <th className="text-left p-2 font-medium">Time</th>
                  <th className="text-left p-2 font-medium">Action</th>
                  <th className="text-left p-2 font-medium">Resource</th>
                  <th className="text-left p-2 font-medium">User</th>
                  <th className="text-left p-2 font-medium">IP</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-t hover:bg-muted/20">
                    <td className="p-2 font-mono text-xs">
                      {new Date(r.ts).toLocaleString()}
                    </td>
                    <td className="p-2">
                      <Badge variant="outline">{r.action}</Badge>
                    </td>
                    <td className="p-2 text-xs">
                      {r.resource_type}
                      {r.resource_id ? ` · ${r.resource_id.slice(0, 8)}` : ""}
                    </td>
                    <td className="p-2 text-xs">
                      {r.user_id ? r.user_id.slice(0, 8) : "—"}
                    </td>
                    <td className="p-2 text-xs">{r.ip ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Retention Tab
// ---------------------------------------------------------------------------

function RetentionTab() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["retention"],
    queryFn: complianceApi.getRetention,
    retry: 1,
  });

  const [defaultDays, setDefaultDays] = useState<number>(365);
  const [legalHold, setLegalHold] = useState<boolean>(false);

  useEffect(() => {
    if (data) {
      setDefaultDays(data.default_days ?? 365);
      setLegalHold(data.legal_hold ?? false);
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      complianceApi.putRetention({
        default_days: defaultDays,
        legal_hold: legalHold,
      }),
    onSuccess: () => {
      toast({ title: "Retention policy saved" });
      queryClient.invalidateQueries({ queryKey: ["retention"] });
    },
    onError: (e: Error) =>
      toast({
        title: "Save failed",
        description: e.message,
        variant: "destructive",
      }),
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  const presets = [
    { label: "30 days", value: 30 },
    { label: "90 days", value: 90 },
    { label: "1 year", value: 365 },
    { label: "Forever", value: 36500 },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data retention</CardTitle>
        <CardDescription>
          How long Vaktram keeps your meeting recordings, transcripts, and
          summaries. A daily worker purges everything older than this — except
          meetings under legal hold.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <Label>Retain everything for</Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {presets.map((p) => (
              <Button
                key={p.value}
                size="sm"
                variant={defaultDays === p.value ? "default" : "outline"}
                className={
                  defaultDays === p.value
                    ? "bg-teal-700 hover:bg-teal-800 text-white"
                    : ""
                }
                onClick={() => setDefaultDays(p.value)}
              >
                {p.label}
              </Button>
            ))}
            <Input
              type="number"
              min={1}
              value={defaultDays}
              onChange={(e) => setDefaultDays(Number(e.target.value) || 0)}
              className="w-32"
            />
            <span className="self-center text-sm text-muted-foreground">days</span>
          </div>
        </div>

        <div className="flex items-start justify-between">
          <div className="space-y-0.5">
            <Label>Legal hold</Label>
            <p className="text-xs text-muted-foreground">
              When enabled, no data is purged regardless of the retention setting.
              Use during audits or active litigation.
            </p>
          </div>
          <Switch checked={legalHold} onCheckedChange={setLegalHold} />
        </div>
      </CardContent>
      <CardFooter>
        <Button
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="bg-teal-700 hover:bg-teal-800 text-white"
        >
          {save.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
          Save policy
        </Button>
      </CardFooter>
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
          <TabsTrigger value="audit" className="gap-2">
            <Shield className="h-4 w-4" />
            Audit log
          </TabsTrigger>
          <TabsTrigger value="retention" className="gap-2">
            <Archive className="h-4 w-4" />
            Retention
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

        <TabsContent value="audit">
          <AuditTab />
        </TabsContent>

        <TabsContent value="retention">
          <RetentionTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
