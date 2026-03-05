"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  getBNetAuthorizeUrl,
  unlinkBNet,
  getLinkedCharacters,
} from "@/lib/bnet-api";
import type { LinkedCharacter } from "@/lib/bnet-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function SettingsPage() {
  const { user, accessToken, isLoading } = useAuth();
  const [characters, setCharacters] = useState<LinkedCharacter[]>([]);
  const [linking, setLinking] = useState(false);
  const [unlinking, setUnlinking] = useState(false);

  useEffect(() => {
    if (accessToken && user?.battle_net_linked) {
      getLinkedCharacters(accessToken)
        .then(setCharacters)
        .catch(() => setCharacters([]));
    }
  }, [accessToken, user?.battle_net_linked]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!user || !accessToken) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">
              Please{" "}
              <Link href="/login" className="text-blue-500 hover:underline">
                log in
              </Link>{" "}
              to access settings.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleLink = async () => {
    setLinking(true);
    try {
      const data = await getBNetAuthorizeUrl(accessToken);
      window.location.href = data.authorize_url;
    } catch {
      setLinking(false);
    }
  };

  const handleUnlink = async () => {
    setUnlinking(true);
    try {
      await unlinkBNet(accessToken);
      setCharacters([]);
      window.location.reload();
    } catch {
      setUnlinking(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div>
            <span className="text-muted-foreground">Email:</span> {user.email}
          </div>
          <div>
            <span className="text-muted-foreground">Display Name:</span>{" "}
            {user.display_name}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Battle.net Linking</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {user.battle_net_linked ? (
            <>
              <div className="text-sm">
                <span className="text-muted-foreground">BattleTag:</span>{" "}
                <span className="font-medium">{user.battletag}</span>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleUnlink}
                disabled={unlinking}
              >
                {unlinking ? "Unlinking..." : "Unlink Battle.net"}
              </Button>
            </>
          ) : (
            <>
              <p className="text-muted-foreground text-sm">
                Link your Battle.net account to verify character ownership and
                unlock additional features.
              </p>
              <Button onClick={handleLink} disabled={linking}>
                {linking ? "Redirecting..." : "Link Battle.net"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {user.battle_net_linked && (
        <Card>
          <CardHeader>
            <CardTitle>
              Verified Characters{" "}
              <span className="text-muted-foreground text-base font-normal">
                ({characters.length})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {characters.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No characters linked yet. Characters will be linked
                automatically when they exist in our database.
              </p>
            ) : (
              <div className="space-y-1">
                {characters.map((char) => (
                  <Link
                    key={`${char.realm}-${char.name}`}
                    href={`/character/${char.realm}/${char.name.toLowerCase()}`}
                    className="hover:bg-muted/50 flex items-center justify-between rounded px-2 py-1.5 text-sm"
                  >
                    <span className="font-medium text-blue-500">
                      {char.name}
                    </span>
                    <span className="text-muted-foreground text-xs">
                      {char.realm} — Level {char.level} {char.class_name}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
