"use client";

import { useEffect, useState } from "react";
import { channelsApi, type Channel } from "@/lib/api/channels";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Plus, Hash, Lock, Trash2 } from "lucide-react";

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => channelsApi.list().then(setChannels).catch((e) => setError(String(e)));

  useEffect(() => {
    refresh();
  }, []);

  const create = async () => {
    if (!name) return;
    setCreating(true);
    setError(null);
    try {
      await channelsApi.create({ name, description: description || undefined, is_private: isPrivate });
      setName("");
      setDescription("");
      setIsPrivate(false);
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    } finally {
      setCreating(false);
    }
  };

  const remove = async (id: string) => {
    await channelsApi.remove(id);
    refresh();
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Hash className="h-6 w-6 text-teal-700" /> Channels
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Group meetings into shared workspaces. Members can browse a channel&apos;s
          meetings and ask Vakta questions scoped to it.
        </p>
      </header>

      <Card className="p-4 space-y-3">
        <div className="grid gap-3 md:grid-cols-2">
          <Input
            placeholder="Channel name (e.g. Sales Calls)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
            />
            Private (invite only)
          </label>
          <Button onClick={create} disabled={creating || !name}>
            <Plus className="h-4 w-4 mr-1" /> Create channel
          </Button>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        {channels.length === 0 ? (
          <p className="text-sm text-muted-foreground col-span-2">
            No channels yet. Create one to start grouping meetings.
          </p>
        ) : (
          channels.map((c) => (
            <Card key={c.id} className="p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-semibold flex items-center gap-2">
                    <Hash className="h-4 w-4 text-muted-foreground" />
                    {c.name}
                    {c.is_private && (
                      <Badge variant="outline" className="text-xs">
                        <Lock className="h-3 w-3 mr-1" /> private
                      </Badge>
                    )}
                  </div>
                  {c.description && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {c.description}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-2 font-mono">
                    /{c.slug}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => remove(c.id)}
                  aria-label="Delete channel"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
