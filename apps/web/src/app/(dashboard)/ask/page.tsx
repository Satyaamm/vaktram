"use client";

import { useEffect, useRef, useState } from "react";
import { askApi, type AskMessage, type AskThreadSummary } from "@/lib/api/ask";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Plus, Send, Sparkles } from "lucide-react";
import { ByomRequired } from "@/components/onboarding/byom-required";

export default function AskPage() {
  const [threads, setThreads] = useState<AskThreadSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AskMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    askApi.listThreads().then(setThreads).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!activeId) return;
    askApi.getThread(activeId).then((t) => setMessages(t.messages));
  }, [activeId]);

  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight });
  }, [messages.length, pending]);

  const startThread = async () => {
    const t = await askApi.createThread({ scope: "organization" });
    setThreads((prev) => [{ id: t.id, title: t.title, scope: t.scope }, ...prev]);
    setActiveId(t.id);
    setMessages([]);
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || !activeId || pending) return;

    setInput("");
    setPending(true);
    setError(null);
    setMessages((prev) => [
      ...prev,
      { id: `tmp-${Date.now()}`, role: "user", content: text },
    ]);
    try {
      const reply = await askApi.send(activeId, text);
      setMessages((prev) => [...prev, reply]);
    } catch (e) {
      if (e instanceof ApiError && e.status === 412) {
        setError(
          "Configure your AI provider in Settings → AI Config to enable Vakta.",
        );
      } else {
        setError(e instanceof Error ? e.message : "Failed to send");
      }
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* thread sidebar */}
      <aside className="w-64 border-r bg-muted/20 flex flex-col">
        <div className="p-3 border-b">
          <Button onClick={startThread} className="w-full" size="sm">
            <Plus className="h-4 w-4 mr-1" /> New chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {threads.length === 0 && (
            <p className="text-xs text-muted-foreground px-2 py-4">
              No conversations yet.
            </p>
          )}
          {threads.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveId(t.id)}
              className={`w-full text-left text-sm px-2 py-2 rounded hover:bg-muted truncate ${
                activeId === t.id ? "bg-muted font-medium" : ""
              }`}
            >
              {t.title || "Untitled chat"}
            </button>
          ))}
        </div>
      </aside>

      {/* conversation */}
      <main className="flex-1 flex flex-col">
        <header className="border-b px-6 py-3 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-teal-700" />
          <div>
            <h1 className="text-lg font-semibold">Ask Vakta</h1>
            <p className="text-xs text-muted-foreground">
              Chat with your meetings — Vakta answers with citations.
            </p>
          </div>
        </header>

        <div ref={messagesRef} className="flex-1 overflow-y-auto p-6 space-y-4">
          <ByomRequired feature="Vakta" />
          {!activeId ? (
            <div className="text-center text-muted-foreground py-16">
              Start a new chat to ask anything about your meetings.
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-16">
              <Sparkles className="h-8 w-8 mx-auto mb-2 text-teal-700" />
              Ask Vakta something — “What did the customer say about pricing?”
            </div>
          ) : (
            messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))
          )}
          {pending && (
            <div className="text-sm text-muted-foreground italic">Vakta is thinking…</div>
          )}
          {error && <div className="text-sm text-destructive">{error}</div>}
        </div>

        <div className="border-t p-3 flex gap-2">
          <Input
            placeholder={
              activeId ? "Ask a question…" : "Start a new chat first"
            }
            value={input}
            disabled={!activeId || pending}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
          />
          <Button
            onClick={sendMessage}
            disabled={!activeId || pending || !input.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </main>
    </div>
  );
}

function MessageBubble({ message }: { message: AskMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <Card
        className={`max-w-2xl px-4 py-3 ${
          isUser ? "bg-teal-700 text-white" : "bg-muted"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3 border-t pt-2 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Sources</p>
            {message.citations.map((c, i) => (
              <a
                key={`${c.segment_id || i}`}
                href={
                  c.meeting_id
                    ? `/meetings/${c.meeting_id}${
                        c.start_time != null ? `?t=${Math.floor(c.start_time)}` : ""
                      }`
                    : "#"
                }
                className="block text-xs text-teal-700 hover:underline"
              >
                [^{i + 1}] {c.meeting_title || "Meeting"}
                {c.speaker_name ? ` · ${c.speaker_name}` : ""}
                {c.start_time != null ? ` @ ${Math.floor(c.start_time)}s` : ""}
                <span className="block text-muted-foreground line-clamp-2 mt-0.5">
                  {c.content}
                </span>
              </a>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
