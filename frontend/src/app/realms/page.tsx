import type { Metadata } from "next";
import { RealmList } from "@/components/RealmList";

export const metadata: Metadata = {
  title: "Realms | chattbc.gg",
  description: "Browse TBC Classic realms by region, type, and population.",
};

const SERVER_API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

interface Realm {
  slug: string;
  name: string;
  type: string;
  region: string;
  population: string;
}

export default async function RealmsPage() {
  let realms: Realm[] = [];
  try {
    const res = await fetch(`${SERVER_API_BASE}/api/realms`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      realms = (await res.json()) as Realm[];
    }
  } catch {
    // API unavailable — render empty
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">TBC Classic Realms</h1>
      <RealmList initialRealms={realms} />
    </div>
  );
}
