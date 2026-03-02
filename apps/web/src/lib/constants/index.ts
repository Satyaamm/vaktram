import {
  LayoutDashboard,
  Video,
  Search,
  BarChart3,
  Settings,
  Users,
} from "lucide-react";

export const APP_NAME = "Vaktram";

export const SUPPORTED_LLM_PROVIDERS = [
  { id: "openai", name: "OpenAI", models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"] },
  { id: "anthropic", name: "Anthropic", models: ["claude-sonnet-4-20250514", "claude-haiku-35-20241022"] },
  { id: "google", name: "Google AI", models: ["gemini-2.0-flash", "gemini-2.5-pro"] },
  { id: "azure", name: "Azure OpenAI", models: [] },
  { id: "ollama", name: "Ollama (Local)", models: ["llama3", "mistral", "mixtral"] },
  { id: "custom", name: "Custom / OpenAI-compatible", models: [] },
] as const;

export const PLAN_LIMITS = {
  free: {
    name: "Free",
    price: 0,
    meetingsPerMonth: 10,
    storageMb: 500,
    maxParticipants: 5,
    features: ["Basic transcription", "AI summaries (BYOM)", "5 meetings/month"],
  },
  pro: {
    name: "Pro",
    price: 19,
    meetingsPerMonth: 100,
    storageMb: 10_000,
    maxParticipants: 25,
    features: [
      "Unlimited transcription",
      "AI summaries & action items",
      "100 meetings/month",
      "Calendar integration",
      "Search across meetings",
    ],
  },
  team: {
    name: "Team",
    price: 49,
    meetingsPerMonth: -1, // unlimited
    storageMb: 100_000,
    maxParticipants: 100,
    features: [
      "Everything in Pro",
      "Unlimited meetings",
      "Team analytics",
      "Shared meeting library",
      "Admin controls",
      "Priority support",
    ],
  },
  enterprise: {
    name: "Enterprise",
    price: -1, // custom
    meetingsPerMonth: -1,
    storageMb: -1,
    maxParticipants: -1,
    features: [
      "Everything in Team",
      "SSO / SAML",
      "Custom integrations",
      "Dedicated support",
      "On-prem deployment option",
      "SLA guarantee",
    ],
  },
} as const;

export const NAV_ITEMS = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Meetings", href: "/meetings", icon: Video },
  { title: "Search", href: "/search", icon: Search },
  { title: "Analytics", href: "/analytics", icon: BarChart3 },
  { title: "Team", href: "/team", icon: Users },
  { title: "Settings", href: "/settings", icon: Settings },
] as const;
