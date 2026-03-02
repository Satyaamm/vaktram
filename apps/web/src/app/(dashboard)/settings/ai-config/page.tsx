"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Brain,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Plus,
  Trash2,
  XCircle,
  Zap,
  Star,
  Pencil,
  Server,
  Cloud,
} from "lucide-react";
import Link from "next/link";

import {
  getAIConfigs,
  createAIConfig,
  updateAIConfig,
  deleteAIConfig,
  testAIConfig,
} from "@/lib/api/settings";
import { SUPPORTED_LLM_PROVIDERS } from "@/lib/constants";
import type { UserAIConfig } from "@/types";
import { useToast } from "@/hooks/use-toast";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const aiConfigSchema = z.object({
  provider: z.string().min(1, "Please select a provider"),
  model: z.string().min(1, "Model name is required"),
  api_key: z.string().min(1, "API key is required"),
  base_url: z.string().optional(),
});

type AIConfigFormValues = z.infer<typeof aiConfigSchema>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const PROVIDER_ICONS: Record<string, typeof Cloud> = {
  openai: Cloud,
  anthropic: Brain,
  google: Zap,
  azure: Cloud,
  ollama: Server,
  custom: Server,
};

function getModelPlaceholder(provider: string): string {
  switch (provider) {
    case "openai":
      return "gpt-4o";
    case "anthropic":
      return "claude-sonnet-4-20250514";
    case "google":
      return "gemini-2.0-flash";
    case "azure":
      return "gpt-4o (deployment name)";
    case "ollama":
      return "llama3";
    case "custom":
      return "model-name";
    default:
      return "model-name";
  }
}

function showBaseUrl(provider: string): boolean {
  return provider === "ollama" || provider === "custom" || provider === "azure";
}

// ---------------------------------------------------------------------------
// Test Result type
// ---------------------------------------------------------------------------

interface TestResult {
  success: boolean;
  message: string;
  response_time_ms?: number;
}

// ---------------------------------------------------------------------------
// Add / Edit Config Form
// ---------------------------------------------------------------------------

function ConfigForm({
  editingConfig,
  onDone,
}: {
  editingConfig?: UserAIConfig | null;
  onDone: () => void;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [showKey, setShowKey] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const form = useForm<AIConfigFormValues>({
    resolver: zodResolver(aiConfigSchema),
    defaultValues: {
      provider: editingConfig?.provider ?? "",
      model: editingConfig?.model ?? "",
      api_key: "",
      base_url: editingConfig?.base_url ?? "",
    },
  });

  const selectedProvider = form.watch("provider");

  const createMutation = useMutation({
    mutationFn: (data: AIConfigFormValues) => createAIConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Configuration saved", description: "Your AI config has been saved." });
      form.reset();
      setTestResult(null);
      onDone();
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to save configuration.",
        variant: "destructive",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: AIConfigFormValues) =>
      updateAIConfig(editingConfig!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Configuration updated" });
      form.reset();
      setTestResult(null);
      onDone();
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to update configuration.",
        variant: "destructive",
      });
    },
  });

  async function handleTest() {
    const values = form.getValues();
    if (!values.provider || !values.model || !values.api_key) {
      toast({
        title: "Missing fields",
        description: "Fill in provider, model, and API key before testing.",
        variant: "destructive",
      });
      return;
    }
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await testAIConfig({
        provider: values.provider,
        model: values.model,
        api_key: values.api_key,
        base_url: values.base_url || undefined,
      });
      setTestResult(result);
    } catch {
      setTestResult({
        success: false,
        message: "Connection test failed. Check your credentials and try again.",
      });
    } finally {
      setIsTesting(false);
    }
  }

  function onSubmit(values: AIConfigFormValues) {
    const payload = {
      ...values,
      base_url: values.base_url || undefined,
    };
    if (editingConfig) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {editingConfig ? "Edit Configuration" : "Add New Configuration"}
        </CardTitle>
        <CardDescription>
          {editingConfig
            ? "Update your LLM provider settings."
            : "Connect a new LLM provider for AI-powered features."}
        </CardDescription>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {/* Provider */}
            <FormField
              control={form.control}
              name="provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Provider</FormLabel>
                  <Select
                    onValueChange={(val) => {
                      field.onChange(val);
                      setTestResult(null);
                    }}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a provider" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {SUPPORTED_LLM_PROVIDERS.map((provider) => {
                        const Icon = PROVIDER_ICONS[provider.id] ?? Cloud;
                        return (
                          <SelectItem key={provider.id} value={provider.id}>
                            <span className="flex items-center gap-2">
                              <Icon className="h-4 w-4" />
                              {provider.name}
                            </span>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Model */}
            <FormField
              control={form.control}
              name="model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Model</FormLabel>
                  <FormControl>
                    <Input
                      placeholder={getModelPlaceholder(selectedProvider)}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Enter the model identifier for your chosen provider.
                    {selectedProvider &&
                      SUPPORTED_LLM_PROVIDERS.find(
                        (p) => p.id === selectedProvider
                      )?.models.length
                      ? ` Suggestions: ${SUPPORTED_LLM_PROVIDERS.find(
                          (p) => p.id === selectedProvider
                        )!.models.join(", ")}`
                      : ""}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* API Key */}
            <FormField
              control={form.control}
              name="api_key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>API Key</FormLabel>
                  <div className="relative">
                    <FormControl>
                      <Input
                        type={showKey ? "text" : "password"}
                        placeholder="sk-..."
                        className="pr-10"
                        {...field}
                      />
                    </FormControl>
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowKey(!showKey)}
                      tabIndex={-1}
                    >
                      {showKey ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  <FormDescription>
                    Your API key is encrypted at rest and never shared.
                    {editingConfig &&
                      " Leave blank to keep the existing key."}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Base URL (conditional) */}
            {showBaseUrl(selectedProvider) && (
              <FormField
                control={form.control}
                name="base_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Base URL{" "}
                      <Badge variant="outline" className="ml-1 text-xs">
                        Optional
                      </Badge>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder={
                          selectedProvider === "ollama"
                            ? "http://localhost:11434/v1"
                            : "https://api.openai.com/v1"
                        }
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Override the API base URL for custom endpoints or local
                      models.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Test result */}
            {testResult && (
              <div
                className={`flex items-center gap-2 rounded-lg border p-3 text-sm ${
                  testResult.success
                    ? "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200"
                    : "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
                }`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 shrink-0" />
                )}
                <span>
                  {testResult.message}
                  {testResult.success && testResult.response_time_ms != null && (
                    <span className="ml-1 text-xs opacity-75">
                      ({testResult.response_time_ms}ms)
                    </span>
                  )}
                </span>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex justify-between">
            <Button
              type="button"
              variant="outline"
              className="gap-2"
              onClick={handleTest}
              disabled={isTesting}
            >
              {isTesting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              Test Connection
            </Button>
            <div className="flex gap-2">
              {editingConfig && (
                <Button type="button" variant="outline" onClick={onDone}>
                  Cancel
                </Button>
              )}
              <Button
                type="submit"
                className="bg-teal-700 hover:bg-teal-800 text-white"
                disabled={isSaving}
              >
                {isSaving && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {editingConfig ? "Update Configuration" : "Save Configuration"}
              </Button>
            </div>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Saved Configurations List
// ---------------------------------------------------------------------------

function SavedConfigsList({
  configs,
  isLoading,
  onEdit,
}: {
  configs: UserAIConfig[];
  isLoading: boolean;
  onEdit: (config: UserAIConfig) => void;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<UserAIConfig | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteAIConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Configuration deleted" });
      setDeleteTarget(null);
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to delete configuration.",
        variant: "destructive",
      });
    },
  });

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => updateAIConfig(id, { is_default: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Default provider updated" });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to set default.",
        variant: "destructive",
      });
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-72 mt-1" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Saved Configurations</CardTitle>
          <CardDescription>
            You can save multiple provider configs and switch between them.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {configs.length === 0 ? (
            <div className="text-center py-8">
              <Brain className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                No configurations saved yet. Add one above to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {configs.map((config) => {
                const Icon = PROVIDER_ICONS[config.provider] ?? Cloud;
                const providerInfo = SUPPORTED_LLM_PROVIDERS.find(
                  (p) => p.id === config.provider
                );
                return (
                  <div
                    key={config.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted">
                        <Icon className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">
                            {providerInfo?.name ?? config.provider} &mdash;{" "}
                            {config.model}
                          </p>
                          {config.is_default && (
                            <Badge className="bg-teal-100 text-teal-800 text-xs">
                              Default
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Added{" "}
                          {new Date(config.created_at).toLocaleDateString(
                            "en-US",
                            {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            }
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!config.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="gap-1"
                          onClick={() => setDefaultMutation.mutate(config.id)}
                          disabled={setDefaultMutation.isPending}
                        >
                          <Star className="h-3 w-3" />
                          Set Default
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1"
                        onClick={() => onEdit(config)}
                      >
                        <Pencil className="h-3 w-3" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1 text-destructive hover:text-destructive"
                        onClick={() => setDeleteTarget(config)}
                      >
                        <Trash2 className="h-3 w-3" />
                        Delete
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete confirmation dialog */}
      <Dialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Configuration</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the{" "}
              <strong>
                {deleteTarget?.provider} &mdash; {deleteTarget?.model}
              </strong>{" "}
              configuration? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function AIConfigPage() {
  const [editingConfig, setEditingConfig] = useState<UserAIConfig | null>(null);
  const [showForm, setShowForm] = useState(true);

  const { data: configs = [], isLoading } = useQuery<UserAIConfig[]>({
    queryKey: ["ai-configs"],
    queryFn: getAIConfigs,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/settings">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            AI Configuration
          </h1>
          <p className="text-muted-foreground mt-1">
            Bring Your Own Model (BYOM) -- connect your preferred LLM provider
            for meeting summaries, action items, and insights.
          </p>
        </div>
      </div>

      {/* Free tier note */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
        <p className="text-sm text-amber-800 dark:text-amber-200">
          <strong>Note:</strong> Free tier uses Gemini 2.0 Flash by default.
          Upgrade to Pro or add your own API key for full BYOM support.
        </p>
      </div>

      {/* Add / Edit form */}
      {showForm || editingConfig ? (
        <ConfigForm
          key={editingConfig?.id ?? "new"}
          editingConfig={editingConfig}
          onDone={() => {
            setEditingConfig(null);
            setShowForm(true);
          }}
        />
      ) : (
        <Button
          className="gap-2 bg-teal-700 hover:bg-teal-800 text-white"
          onClick={() => setShowForm(true)}
        >
          <Plus className="h-4 w-4" />
          Add New Configuration
        </Button>
      )}

      {/* Saved configurations */}
      <SavedConfigsList
        configs={configs}
        isLoading={isLoading}
        onEdit={(config) => {
          setEditingConfig(config);
          setShowForm(false);
        }}
      />
    </div>
  );
}
