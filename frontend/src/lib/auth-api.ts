import { apiFetch } from "@/lib/api-client";

export interface User {
  id: number;
  email: string;
  display_name: string;
  email_verified: boolean;
  battle_net_linked: boolean;
  battletag: string | null;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MessageResponse {
  detail: string;
}

export function register(
  email: string,
  password: string,
  displayName: string,
): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: displayName,
    }),
  });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function refreshAccessToken(
  refreshToken: string,
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function getMe(accessToken: string): Promise<User> {
  return apiFetch<User>("/api/auth/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function forgotPassword(email: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(
  token: string,
  newPassword: string,
): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}
