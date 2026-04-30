"use client";

import { useEffect, useState } from "react";
import { topicsApi, type TopicHit, type TopicTracker } from "@/lib/api/topics";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Trash2, Plus, Hash, Bell } from "lucide-react";

export default function TopicsPage() {
  const [trackers, setTrackers] = useState<TopicTracker[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [hits, setHits] = useState<TopicHit[]>([]);
  const [newName, setNewName] = useState("");
  const [newKeywords, setNewKeywords] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => topicsApi.list().then(setTrackers);

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (!activeId) {
      setHits([]);
      return;
    }
    topicsApi.hits(activeId).then(setHits);
  }, [activeId]);

  const create = async () => {
    const keywords = newKeywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);
    if (!newName || keywords.length === 0) return;
    setCreating(true);
    setError(null);
    try {
      await topicsApi.create({ name: newName, keywords });
      setNewName("");
      setNewKeywords("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    } finally {
      setCreating(false);
    }
  };

  const remove = async (id: string) => {
    await topicsApi.remove(id);
    if (id === activeId) setActiveId(null);
    refresh();
  };

  const toggle = async (t: TopicTracker) => {
    await topicsApi.update(t.id, { is_active: !t.is_active });
    refresh();
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Hash className="h-6 w-6 text-teal-700" /> Topic Tracker
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Get notified every time a keyword is mentioned across your meetings.
        </p>
      </header>

      <Card className="p-4">
        <div className="grid gap-3 md:grid-cols-[1fr_2fr_auto]">
          <Input
            placeholder="Tracker name (e.g. Pricing)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <Input
            placeholder="Keywords, comma-separated (pricing, discount, contract)"
            value={newKeywords}
            onChange={(e) => setNewKeywords(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") create();
            }}
          />
          <Button onClick={create} disabled={creating || !newName || !newKeywords}>
            <Plus className="h-4 w-4 mr-1" /> Create
          </Button>
        </div>
        {error && <p className="text-sm text-destructive mt-2">{error}</p>}
      </Card>

      <div className="grid gap-6 md:grid-cols-[1fr_2fr]">
        <section>
          <h2 className="text-sm font-medium mb-2">Trackers</h2>
          <div className="space-y-2">
            {trackers.length === 0 && (
              <p className="text-sm text-muted-foreground">No trackers yet.</p>
            )}
            {trackers.map((t) => (
              <Card
                key={t.id}
                className={`p-3 cursor-pointer transition ${
                  activeId === t.id ? "ring-2 ring-teal-700" : ""
                }`}
                onClick={() => setActiveId(t.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-medium flex items-center gap-2">
                      {t.name}
                      {!t.is_active && (
                        <Badge variant="outline" className="text-xs">
                          paused
                        </Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {t.keywords.map((k) => (
                        <Badge key={k} variant="secondary" className="text-xs">
                          {k}
                        </Badge>
                      ))}
                    </div>
                    {t.notify_emails.length > 0 && (
                      <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                        <Bell className="h-3 w-3" /> {t.notify_emails.join(", ")}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggle(t);
                      }}
                    >
                      {t.is_active ? "Pause" : "Resume"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        remove(t.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium mb-2">
            {activeId ? "Recent hits" : "Pick a tracker to see hits"}
          </h2>
          <div className="space-y-2">
            {activeId && hits.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No matches yet — Vaktram will populate this as new meetings finish.
              </p>
            )}
            {hits.map((h) => (
              <Card key={h.id} className="p-3">
                <div className="text-xs text-muted-foreground flex items-center gap-2">
                  <Badge variant="outline">{h.matched_keyword}</Badge>
                  <a
                    href={`/meetings/${h.meeting_id}${
                      h.timestamp != null ? `?t=${Math.floor(h.timestamp)}` : ""
                    }`}
                    className="text-teal-700 hover:underline"
                  >
                    Open meeting
                  </a>
                  {h.timestamp != null && (
                    <span>@ {Math.floor(h.timestamp)}s</span>
                  )}
                </div>
                <p className="text-sm mt-1">{h.snippet}</p>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
