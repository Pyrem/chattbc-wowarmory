import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function CharacterNotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-4xl font-bold">Character Not Found</h1>
      <p className="text-muted-foreground max-w-md">
        The character you&apos;re looking for doesn&apos;t exist or hasn&apos;t
        been indexed yet. Check the realm and name, then try again.
      </p>
      <Link href="/">
        <Button>Back to Home</Button>
      </Link>
    </div>
  );
}
