"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface RosterMember {
  character?: {
    name?: string;
    level?: number;
    playable_class?: { name?: string };
    playable_race?: { name?: string };
    realm?: { slug?: string };
  };
  rank?: number;
}

interface GuildRosterProps {
  roster: Record<string, unknown>;
  realm: string;
}

type SortKey = "name" | "level" | "rank" | "class";

const RANK_LABELS: Record<number, string> = {
  0: "Guild Master",
  1: "Officer",
};

export function GuildRoster({ roster, realm }: GuildRosterProps) {
  const members = (roster.members ?? []) as RosterMember[];
  const [sortKey, setSortKey] = useState<SortKey>("rank");
  const [sortAsc, setSortAsc] = useState(true);

  if (members.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Roster</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            No roster data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const sorted = [...members].sort((a, b) => {
    let cmp = 0;
    switch (sortKey) {
      case "name":
        cmp = (a.character?.name ?? "").localeCompare(b.character?.name ?? "");
        break;
      case "level":
        cmp = (a.character?.level ?? 0) - (b.character?.level ?? 0);
        break;
      case "rank":
        cmp = (a.rank ?? 99) - (b.rank ?? 99);
        break;
      case "class":
        cmp = (a.character?.playable_class?.name ?? "").localeCompare(
          b.character?.playable_class?.name ?? "",
        );
        break;
    }
    return sortAsc ? cmp : -cmp;
  });

  const arrow = (key: SortKey) => {
    if (sortKey !== key) return "";
    return sortAsc ? " ▲" : " ▼";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Roster{" "}
          <span className="text-muted-foreground text-base font-normal">
            ({members.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted-foreground border-b text-left text-xs">
                <SortHeader
                  label="Name"
                  sortKey="name"
                  arrow={arrow}
                  onClick={handleSort}
                />
                <SortHeader
                  label="Level"
                  sortKey="level"
                  arrow={arrow}
                  onClick={handleSort}
                />
                <SortHeader
                  label="Class"
                  sortKey="class"
                  arrow={arrow}
                  onClick={handleSort}
                />
                <SortHeader
                  label="Rank"
                  sortKey="rank"
                  arrow={arrow}
                  onClick={handleSort}
                />
              </tr>
            </thead>
            <tbody>
              {sorted.map((member, idx) => {
                const charName = member.character?.name ?? "Unknown";
                const charRealm = member.character?.realm?.slug ?? realm;

                return (
                  <tr
                    key={idx}
                    className="hover:bg-muted/50 border-b last:border-0"
                  >
                    <td className="py-1.5 pr-4">
                      <Link
                        href={`/character/${encodeURIComponent(charRealm)}/${encodeURIComponent(charName.toLowerCase())}`}
                        className="font-medium text-blue-500 hover:underline"
                      >
                        {charName}
                      </Link>
                    </td>
                    <td className="py-1.5 pr-4">
                      {member.character?.level ?? "?"}
                    </td>
                    <td className="py-1.5 pr-4">
                      {member.character?.playable_class?.name ?? "—"}
                    </td>
                    <td className="py-1.5">
                      {RANK_LABELS[member.rank ?? -1] ??
                        `Rank ${member.rank ?? "?"}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function SortHeader({
  label,
  sortKey,
  arrow,
  onClick,
}: {
  label: string;
  sortKey: SortKey;
  arrow: (key: SortKey) => string;
  onClick: (key: SortKey) => void;
}) {
  return (
    <th
      className="cursor-pointer py-2 pr-4 select-none"
      onClick={() => onClick(sortKey)}
    >
      {label}
      {arrow(sortKey)}
    </th>
  );
}
