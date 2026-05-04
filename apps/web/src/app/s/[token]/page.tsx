// Public soundbite share page — no auth, no dashboard chrome.

import { notFound } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PublicSoundbite {
  title: string | null;
  start: number;
  end: number;
  transcript: string | null;
}

async function fetchSoundbite(token: string): Promise<PublicSoundbite | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/soundbites/shared/${token}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as PublicSoundbite;
  } catch {
    return null;
  }
}

export default async function SharedSoundbitePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const sb = await fetchSoundbite(token);
  if (!sb) notFound();

  const duration = Math.max(0, sb.end - sb.start);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-2xl px-6 py-16">
        <div className="flex items-center gap-2 mb-8">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-700 text-white font-bold text-sm">
            V
          </div>
          <span className="text-lg font-bold text-teal-700">Vaktram</span>
        </div>

        <h1 className="text-3xl font-bold mb-2">
          {sb.title || "Shared soundbite"}
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          {duration.toFixed(0)} second clip from a meeting
        </p>

        {sb.transcript && (
          <blockquote className="border-l-4 border-teal-700 pl-4 italic text-slate-700 leading-relaxed">
            {sb.transcript}
          </blockquote>
        )}

        <div className="mt-12 text-xs text-muted-foreground">
          Powered by{" "}
          <a
            href={process.env.NEXT_PUBLIC_WEBSITE_URL || "https://vaktram-website.vercel.app"}
            className="text-teal-700 hover:underline"
          >
            Vaktram
          </a>{" "}
          — AI meeting intelligence.
        </div>
      </div>
    </main>
  );
}
