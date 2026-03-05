import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight">chattbc.gg</h1>
        <p className="text-muted-foreground max-w-md text-lg">
          TBC-era World of Warcraft armory, AI chatbot, and community platform.
        </p>
      </div>
      <div className="flex gap-4">
        <Button variant="default" size="lg">
          Search Characters
        </Button>
        <Button variant="outline" size="lg">
          Browse Guilds
        </Button>
      </div>
    </div>
  );
}
