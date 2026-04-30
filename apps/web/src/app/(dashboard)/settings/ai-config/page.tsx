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
import { Textarea } from "@/components/ui/textarea";
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
// Provider config — what each provider needs (from their docs + LiteLLM docs)
// ---------------------------------------------------------------------------

interface ProviderFieldDef {
  key: string;
  label: string;
  placeholder: string;
  description: string;
  required: boolean;
  type: "text" | "password" | "textarea";
  /** If true, stored in extra_config instead of top-level */
  isExtra?: boolean;
}

/** Per-provider field definitions derived from LiteLLM docs */
function getProviderFields(provider: string): ProviderFieldDef[] {
  switch (provider) {
    case "openai":
      return [
        {
          key: "api_key",
          label: "API Key",
          placeholder: "sk-...",
          description: "Your OpenAI API key from platform.openai.com/api-keys",
          required: true,
          type: "password",
        },
      ];

    case "anthropic":
      return [
        {
          key: "api_key",
          label: "API Key",
          placeholder: "sk-ant-...",
          description: "Your Anthropic API key from console.anthropic.com/settings/keys",
          required: true,
          type: "password",
        },
      ];

    case "gemini":
      return [
        {
          key: "api_key",
          label: "API Key",
          placeholder: "AI...",
          description: "Your Google AI API key from aistudio.google.com/apikey",
          required: true,
          type: "password",
        },
      ];

    case "azure":
      // Azure OpenAI: needs endpoint, api_key, api_version, deployment name (as model)
      return [
        {
          key: "base_url",
          label: "Azure Endpoint",
          placeholder: "https://your-resource.openai.azure.com",
          description: "Your Azure OpenAI resource endpoint URL",
          required: true,
          type: "text",
        },
        {
          key: "api_key",
          label: "API Key",
          placeholder: "your-azure-api-key",
          description: "Azure OpenAI API key (found in Azure Portal > Keys and Endpoint)",
          required: true,
          type: "password",
        },
        {
          key: "api_version",
          label: "API Version",
          placeholder: "2024-06-01",
          description: "Azure OpenAI API version (e.g. 2024-06-01, 2024-02-15-preview)",
          required: true,
          type: "text",
          isExtra: true,
        },
      ];

    case "azure_ai":
      // Azure AI Studio: needs endpoint + key
      return [
        {
          key: "base_url",
          label: "Inference Endpoint",
          placeholder: "https://your-model-serverless.eastus2.inference.ai.azure.com",
          description: "Your Azure AI Studio model inference endpoint URL",
          required: true,
          type: "text",
        },
        {
          key: "api_key",
          label: "API Key",
          placeholder: "your-azure-ai-key",
          description: "Azure AI Studio inference key",
          required: true,
          type: "password",
        },
      ];

    case "bedrock":
      // AWS Bedrock: aws_access_key_id, aws_secret_access_key, aws_region_name
      return [
        {
          key: "aws_access_key_id",
          label: "AWS Access Key ID",
          placeholder: "AKIA...",
          description: "Your AWS IAM access key ID with Bedrock permissions",
          required: true,
          type: "text",
          isExtra: true,
        },
        {
          key: "aws_secret_access_key",
          label: "AWS Secret Access Key",
          placeholder: "your-secret-key",
          description: "Your AWS IAM secret access key",
          required: true,
          type: "password",
          isExtra: true,
        },
        {
          key: "aws_region_name",
          label: "AWS Region",
          placeholder: "us-east-1",
          description: "AWS region where Bedrock is enabled (e.g. us-east-1, us-west-2)",
          required: true,
          type: "text",
          isExtra: true,
        },
      ];

    case "vertex_ai":
      // GCP Vertex AI: vertex_project, vertex_location, vertex_credentials (JSON)
      return [
        {
          key: "vertex_project",
          label: "GCP Project ID",
          placeholder: "my-gcp-project-12345",
          description: "Your Google Cloud project ID",
          required: true,
          type: "text",
          isExtra: true,
        },
        {
          key: "vertex_location",
          label: "Region",
          placeholder: "us-central1",
          description: "GCP region (e.g. us-central1, europe-west4)",
          required: true,
          type: "text",
          isExtra: true,
        },
        {
          key: "vertex_credentials",
          label: "Service Account JSON",
          placeholder: '{"type": "service_account", "project_id": "...", ...}',
          description: "Paste the full JSON content of your GCP service account key file",
          required: true,
          type: "textarea",
          isExtra: true,
        },
      ];

    case "groq":
      return [
        {
          key: "api_key",
          label: "API Key",
          placeholder: "gsk_...",
          description: "Your Groq API key from console.groq.com/keys",
          required: true,
          type: "password",
        },
      ];

    case "ollama":
      // Ollama: just the server URL, no API key needed
      return [
        {
          key: "base_url",
          label: "Ollama Server URL",
          placeholder: "http://localhost:11434",
          description: "Your Ollama server URL (default: http://localhost:11434)",
          required: true,
          type: "text",
        },
      ];

    case "custom":
      // Custom OpenAI-compatible: base_url + api_key
      return [
        {
          key: "base_url",
          label: "API Base URL",
          placeholder: "https://your-api.example.com/v1",
          description: "Base URL of your OpenAI-compatible API endpoint",
          required: true,
          type: "text",
        },
        {
          key: "api_key",
          label: "API Key",
          placeholder: "your-api-key",
          description: "API key for authentication (if required)",
          required: false,
          type: "password",
        },
      ];

    default:
      return [
        {
          key: "api_key",
          label: "API Key",
          placeholder: "your-api-key",
          description: "API key for the provider",
          required: true,
          type: "password",
        },
      ];
  }
}

function getModelPlaceholder(provider: string): string {
  switch (provider) {
    case "openai": return "gpt-4o";
    case "anthropic": return "claude-sonnet-4-20250514";
    case "gemini": return "gemini-2.0-flash";
    case "azure": return "your-deployment-name";
    case "azure_ai": return "model-deployment-name";
    case "bedrock": return "anthropic.claude-sonnet-4-20250514-v1:0";
    case "vertex_ai": return "gemini-2.0-flash";
    case "groq": return "llama-3.3-70b-versatile";
    case "ollama": return "llama3";
    case "custom": return "model-name";
    default: return "model-name";
  }
}

function getModelDescription(provider: string): string {
  switch (provider) {
    case "azure": return "Use your Azure deployment name (not the model name).";
    case "bedrock": return "Use the full Bedrock model ID (e.g. anthropic.claude-sonnet-4-20250514-v1:0).";
    case "vertex_ai": return "Use the Vertex AI model name (e.g. gemini-2.0-flash).";
    default: return "Enter the model identifier for your chosen provider.";
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const PROVIDER_ICONS: Record<string, typeof Cloud> = {
  openai: Cloud,
  anthropic: Brain,
  gemini: Zap,
  azure: Cloud,
  azure_ai: Cloud,
  bedrock: Cloud,
  vertex_ai: Cloud,
  groq: Zap,
  ollama: Server,
  custom: Server,
};

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
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // Dynamic form — we use uncontrolled state for provider-specific fields
  const [selectedProvider, setSelectedProvider] = useState(editingConfig?.provider ?? "");
  const [modelName, setModelName] = useState(editingConfig?.model_name ?? "");
  // Field values keyed by field key
  const [fieldValues, setFieldValues] = useState<Record<string, string>>(() => {
    const vals: Record<string, string> = {};
    if (editingConfig?.base_url) vals.base_url = editingConfig.base_url;
    if (editingConfig?.extra_config) {
      Object.entries(editingConfig.extra_config).forEach(([k, v]) => {
        vals[k] = v;
      });
    }
    return vals;
  });
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const providerFields = getProviderFields(selectedProvider);

  const setFieldValue = (key: string, value: string) => {
    setFieldValues((prev) => ({ ...prev, [key]: value }));
    setTestResult(null);
  };

  const toggleSecret = (key: string) => {
    setShowSecrets((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Validation
  function validate(): string | null {
    if (!selectedProvider) return "Please select a provider.";
    if (!modelName.trim()) return "Model name is required.";
    for (const field of providerFields) {
      if (field.required && !fieldValues[field.key]?.trim()) {
        return `${field.label} is required.`;
      }
    }
    return null;
  }

  // Build payload
  function buildPayload() {
    const extra_config: Record<string, string> = {};
    let api_key: string | undefined;
    let base_url: string | undefined;

    for (const field of providerFields) {
      const val = fieldValues[field.key]?.trim();
      if (!val) continue;

      if (field.key === "api_key") {
        api_key = val;
      } else if (field.key === "base_url") {
        base_url = val;
      } else if (field.isExtra) {
        extra_config[field.key] = val;
      }
    }

    return {
      provider: selectedProvider,
      model_name: modelName.trim(),
      api_key,
      base_url,
      extra_config: Object.keys(extra_config).length > 0 ? extra_config : undefined,
    };
  }

  const createMutation = useMutation({
    mutationFn: (data: ReturnType<typeof buildPayload> & { is_default?: boolean }) =>
      createAIConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Configuration saved", description: "Your AI config has been saved." });
      onDone();
    },
    onError: () => {
      toast({ title: "Error", description: "Failed to save configuration.", variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: ReturnType<typeof buildPayload>) =>
      updateAIConfig(editingConfig!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Configuration updated" });
      onDone();
    },
    onError: () => {
      toast({ title: "Error", description: "Failed to update configuration.", variant: "destructive" });
    },
  });

  async function handleTest() {
    const err = validate();
    if (err) {
      toast({ title: "Missing fields", description: err, variant: "destructive" });
      return;
    }
    setIsTesting(true);
    setTestResult(null);
    try {
      const payload = buildPayload();
      const result = await testAIConfig({
        provider: payload.provider,
        model_name: payload.model_name,
        api_key: payload.api_key,
        base_url: payload.base_url,
        extra_config: payload.extra_config,
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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validate();
    if (err) {
      toast({ title: "Validation error", description: err, variant: "destructive" });
      return;
    }
    const payload = buildPayload();
    if (editingConfig) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate({ ...payload, is_default: true });
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
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {/* Provider Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Provider</label>
            <Select
              value={selectedProvider}
              onValueChange={(val) => {
                setSelectedProvider(val);
                setFieldValues({});
                setTestResult(null);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a provider" />
              </SelectTrigger>
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
          </div>

          {/* Model Name */}
          {selectedProvider && (
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {selectedProvider === "azure" ? "Deployment Name" : "Model"}
              </label>
              <Input
                value={modelName}
                onChange={(e) => {
                  setModelName(e.target.value);
                  setTestResult(null);
                }}
                placeholder={getModelPlaceholder(selectedProvider)}
              />
              <p className="text-xs text-muted-foreground">
                {getModelDescription(selectedProvider)}
                {SUPPORTED_LLM_PROVIDERS.find((p) => p.id === selectedProvider)?.models.length
                  ? ` Suggestions: ${SUPPORTED_LLM_PROVIDERS.find(
                      (p) => p.id === selectedProvider
                    )!.models.join(", ")}`
                  : ""}
              </p>
            </div>
          )}

          {/* Provider-specific fields */}
          {selectedProvider &&
            providerFields.map((field) => (
              <div key={field.key} className="space-y-2">
                <label className="text-sm font-medium">
                  {field.label}
                  {!field.required && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      Optional
                    </Badge>
                  )}
                </label>
                {field.type === "textarea" ? (
                  <Textarea
                    value={fieldValues[field.key] ?? ""}
                    onChange={(e) => setFieldValue(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    rows={4}
                    className="font-mono text-xs"
                  />
                ) : (
                  <div className="relative">
                    <Input
                      type={
                        field.type === "password" && !showSecrets[field.key]
                          ? "password"
                          : "text"
                      }
                      value={fieldValues[field.key] ?? ""}
                      onChange={(e) => setFieldValue(field.key, e.target.value)}
                      placeholder={
                        editingConfig && field.key === "api_key"
                          ? "Leave blank to keep existing key"
                          : field.placeholder
                      }
                      className={field.type === "password" ? "pr-10" : ""}
                    />
                    {field.type === "password" && (
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        onClick={() => toggleSecret(field.key)}
                        tabIndex={-1}
                      >
                        {showSecrets[field.key] ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  {editingConfig && field.key === "api_key"
                    ? `${field.description}. Leave blank to keep the existing key.`
                    : field.description}
                </p>
              </div>
            ))}

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
            disabled={isTesting || !selectedProvider}
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
              disabled={isSaving || !selectedProvider}
            >
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {editingConfig ? "Update Configuration" : "Save Configuration"}
            </Button>
          </div>
        </CardFooter>
      </form>
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
      toast({ title: "Error", description: "Failed to delete configuration.", variant: "destructive" });
    },
  });

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => updateAIConfig(id, { is_default: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-configs"] });
      toast({ title: "Default provider updated" });
    },
    onError: () => {
      toast({ title: "Error", description: "Failed to set default.", variant: "destructive" });
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
                            {config.model_name}
                          </p>
                          {config.is_default && (
                            <Badge className="bg-teal-100 text-teal-800 text-xs">
                              Default
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Added{" "}
                          {new Date(config.created_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                          {config.base_url && (
                            <span className="ml-2 text-muted-foreground/60">
                              {config.base_url}
                            </span>
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
                {deleteTarget?.provider} &mdash; {deleteTarget?.model_name}
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

      {/* BYOM required notice */}
      {configs.length === 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <strong>Required:</strong> You must configure an AI model to use
            meeting summaries, action items, and insights. Add your provider
            credentials below to get started.
          </p>
        </div>
      )}

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
