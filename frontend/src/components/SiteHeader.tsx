import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";

export function SiteHeader() {
  return (
    <header className="border-border border-b">
      <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-3">
        <Link href="/" className="shrink-0 text-lg font-bold">
          chattbc.gg
        </Link>
        <SearchBar />
        <nav className="flex shrink-0 gap-3 text-sm">
          <Link
            href="/realms"
            className="text-muted-foreground hover:text-foreground"
          >
            Realms
          </Link>
          <Link
            href="/settings"
            className="text-muted-foreground hover:text-foreground"
          >
            Settings
          </Link>
        </nav>
      </div>
    </header>
  );
}
