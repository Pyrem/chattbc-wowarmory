"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface Realm {
  slug: string;
  name: string;
  type: string;
  region: string;
  population: string;
}

const POPULATION_COLORS: Record<string, string> = {
  High: "text-green-500",
  Medium: "text-yellow-500",
  Low: "text-red-500",
};

interface RealmListProps {
  initialRealms: Realm[];
}

export function RealmList({ initialRealms }: RealmListProps) {
  const [filter, setFilter] = useState("");
  const [regionFilter, setRegionFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const regions = [...new Set(initialRealms.map((r) => r.region))].sort();
  const types = [...new Set(initialRealms.map((r) => r.type))].sort();

  const filtered = initialRealms.filter((realm) => {
    if (filter && !realm.name.toLowerCase().includes(filter.toLowerCase())) {
      return false;
    }
    if (regionFilter !== "all" && realm.region !== regionFilter) {
      return false;
    }
    if (typeFilter !== "all" && realm.type !== typeFilter) {
      return false;
    }
    return true;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Realms{" "}
          <span className="text-muted-foreground text-base font-normal">
            ({filtered.length})
          </span>
        </CardTitle>
        <div className="flex flex-wrap gap-3 pt-2">
          <Input
            type="search"
            placeholder="Filter by name..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-48"
          />
          <select
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
            className="border-input bg-background rounded-md border px-3 py-2 text-sm"
          >
            <option value="all">All Regions</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="border-input bg-background rounded-md border px-3 py-2 text-sm"
          >
            <option value="all">All Types</option>
            {types.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </CardHeader>
      <CardContent>
        {filtered.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No realms match your filters.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground border-b text-left text-xs">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Region</th>
                  <th className="py-2">Population</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((realm) => (
                  <tr
                    key={realm.slug}
                    className="hover:bg-muted/50 border-b last:border-0"
                  >
                    <td className="py-1.5 pr-4">
                      <Link
                        href={`/character/${realm.slug}/`}
                        className="font-medium text-blue-500 hover:underline"
                      >
                        {realm.name}
                      </Link>
                    </td>
                    <td className="text-muted-foreground py-1.5 pr-4">
                      {realm.type}
                    </td>
                    <td className="text-muted-foreground py-1.5 pr-4">
                      {realm.region}
                    </td>
                    <td className="py-1.5">
                      <span
                        className={
                          POPULATION_COLORS[realm.population] ?? "text-gray-500"
                        }
                      >
                        {realm.population}
                      </span>
                    </td>
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
