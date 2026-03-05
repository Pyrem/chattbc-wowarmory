"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";

interface SearchResult {
  type: string;
  name: string;
  realm: string;
  url: string;
  detail: string;
}

interface SearchResponse {
  results: SearchResult[];
  query: string;
  total: number;
}

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await apiFetch<SearchResponse>(
          `/api/search?q=${encodeURIComponent(query)}`,
        );
        setResults(data.results);
        setOpen(data.results.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (result: SearchResult) => {
    setOpen(false);
    setQuery("");
    router.push(result.url);
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-md">
      <Input
        type="search"
        placeholder="Search characters or guilds..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        className="w-full"
      />
      {loading && (
        <div className="text-muted-foreground absolute top-1/2 right-3 -translate-y-1/2 text-xs">
          ...
        </div>
      )}
      {open && (
        <div className="bg-popover border-border absolute top-full z-50 mt-1 w-full overflow-hidden rounded-md border shadow-lg">
          {results.map((result, idx) => (
            <button
              key={idx}
              type="button"
              className="hover:bg-muted flex w-full flex-col px-3 py-2 text-left"
              onClick={() => handleSelect(result)}
            >
              <div className="flex items-center gap-2">
                <span className="bg-muted rounded px-1.5 py-0.5 text-xs font-medium">
                  {result.type}
                </span>
                <span className="truncate text-sm font-medium">
                  {result.name}
                </span>
                <span className="text-muted-foreground text-xs">
                  {result.realm}
                </span>
              </div>
              <span className="text-muted-foreground mt-0.5 text-xs">
                {result.detail}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
