"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search as SearchIcon, Loader2 } from "lucide-react";
import { searchMeetings } from "@/lib/api/meetings";
import type { SearchResult } from "@/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

type FilterType = "transcripts" | "summaries" | "action_items";

function formatTimestamp(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function highlightMatch(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;

  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);

  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark key={i} className="bg-amber-200 text-amber-900 rounded px-0.5">
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

function SearchResultsSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-3 w-32 mt-1" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4 mt-1" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function SearchPage() {
  const [searchInput, setSearchInput] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [activeFilters, setActiveFilters] = useState<Set<FilterType>>(
    new Set<FilterType>(["transcripts", "summaries", "action_items"])
  );

  // Debounce search input by 500ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchInput.trim());
    }, 500);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const {
    data: results,
    isLoading,
    isFetching,
  } = useQuery<SearchResult[]>({
    queryKey: ["search", debouncedQuery],
    queryFn: async () => {
      const data = await searchMeetings(debouncedQuery);
      return data.results;
    },
    enabled: debouncedQuery.length > 0,
  });

  function toggleFilter(filter: FilterType) {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(filter)) {
        next.delete(filter);
      } else {
        next.add(filter);
      }
      return next;
    });
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setDebouncedQuery(searchInput.trim());
  }

  const hasSearched = debouncedQuery.length > 0;
  const hasResults = results && results.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Search</h1>
        <p className="text-muted-foreground mt-1">
          Search across all your meeting transcripts and summaries.
        </p>
      </div>

      {/* Search Input */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search transcripts, summaries, action items..."
                className="pl-9 h-11"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
            <Button
              type="submit"
              className="bg-teal-700 hover:bg-teal-800 text-white h-11 px-6"
              disabled={!searchInput.trim()}
            >
              {isFetching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Search"
              )}
            </Button>
          </form>
          <div className="flex gap-2 mt-3">
            <Badge
              variant={activeFilters.has("transcripts") ? "default" : "outline"}
              className={`cursor-pointer ${
                activeFilters.has("transcripts")
                  ? "bg-teal-700 hover:bg-teal-800 text-white"
                  : "hover:bg-muted"
              }`}
              onClick={() => toggleFilter("transcripts")}
            >
              Transcripts
            </Badge>
            <Badge
              variant={activeFilters.has("summaries") ? "default" : "outline"}
              className={`cursor-pointer ${
                activeFilters.has("summaries")
                  ? "bg-teal-700 hover:bg-teal-800 text-white"
                  : "hover:bg-muted"
              }`}
              onClick={() => toggleFilter("summaries")}
            >
              Summaries
            </Badge>
            <Badge
              variant={
                activeFilters.has("action_items") ? "default" : "outline"
              }
              className={`cursor-pointer ${
                activeFilters.has("action_items")
                  ? "bg-teal-700 hover:bg-teal-800 text-white"
                  : "hover:bg-muted"
              }`}
              onClick={() => toggleFilter("action_items")}
            >
              Action Items
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {isLoading ? (
        <SearchResultsSkeleton />
      ) : hasSearched && hasResults ? (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Showing {results.length} result{results.length !== 1 ? "s" : ""} for
            &ldquo;{debouncedQuery}&rdquo;
          </p>
          {results.map((result) => (
            <Link
              key={`${result.meeting_id}-${result.segment_id}`}
              href={`/meetings/${result.meeting_id}?t=${Math.floor(result.start_time)}`}
            >
              <Card className="cursor-pointer transition-colors hover:bg-muted/50 mb-4">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base text-teal-700 dark:text-teal-500">
                      {result.meeting_title}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs font-normal">
                      {formatTimestamp(result.start_time)}
                    </Badge>
                  </div>
                  <CardDescription className="text-xs">
                    {result.speaker_name} at{" "}
                    {formatTimestamp(result.start_time)} &ndash;{" "}
                    {formatTimestamp(result.end_time)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {highlightMatch(result.content, debouncedQuery)}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : hasSearched && !hasResults ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <SearchIcon className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground">
            No results found for &ldquo;{debouncedQuery}&rdquo;
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <SearchIcon className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground">
            Search across all your meetings.
          </p>
        </div>
      )}
    </div>
  );
}
