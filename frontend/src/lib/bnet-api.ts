import { apiFetch } from "@/lib/api-client";

export interface BNetAuthorizeResponse {
  authorize_url: string;
  state: string;
}

export interface BNetStatusResponse {
  linked: boolean;
  battletag: string | null;
  characters_linked: number;
}

export interface LinkedCharacter {
  name: string;
  realm: string;
  class_name: string;
  level: number;
  faction: string;
}

export function getBNetAuthorizeUrl(
  accessToken: string,
): Promise<BNetAuthorizeResponse> {
  return apiFetch<BNetAuthorizeResponse>("/api/auth/bnet/authorize", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function unlinkBNet(accessToken: string): Promise<BNetStatusResponse> {
  return apiFetch<BNetStatusResponse>("/api/auth/bnet/unlink", {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function getLinkedCharacters(
  accessToken: string,
): Promise<LinkedCharacter[]> {
  return apiFetch<LinkedCharacter[]>("/api/auth/bnet/characters", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
