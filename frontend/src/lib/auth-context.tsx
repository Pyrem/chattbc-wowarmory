"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import type { AuthResponse, User } from "@/lib/auth-api";
import {
  getMe,
  login as apiLogin,
  register as apiRegister,
  refreshAccessToken,
} from "@/lib/auth-api";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName: string,
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function storeTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

function handleAuthResponse(data: AuthResponse): {
  user: User;
  accessToken: string;
} {
  storeTokens(data.access_token, data.refresh_token);
  return { user: data.user, accessToken: data.access_token };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    isLoading: true,
  });

  useEffect(() => {
    const init = async () => {
      const storedAccess = localStorage.getItem("access_token");
      const storedRefresh = localStorage.getItem("refresh_token");

      if (!storedAccess && !storedRefresh) {
        setState({ user: null, accessToken: null, isLoading: false });
        return;
      }

      try {
        if (storedAccess) {
          const user = await getMe(storedAccess);
          setState({ user, accessToken: storedAccess, isLoading: false });
          return;
        }
      } catch {
        // Access token expired, try refresh
      }

      if (storedRefresh) {
        try {
          const tokenData = await refreshAccessToken(storedRefresh);
          localStorage.setItem("access_token", tokenData.access_token);
          const user = await getMe(tokenData.access_token);
          setState({
            user,
            accessToken: tokenData.access_token,
            isLoading: false,
          });
          return;
        } catch {
          clearTokens();
        }
      }

      setState({ user: null, accessToken: null, isLoading: false });
    };

    init();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    const { user, accessToken } = handleAuthResponse(data);
    setState({ user, accessToken, isLoading: false });
  }, []);

  const register = useCallback(
    async (email: string, password: string, displayName: string) => {
      const data = await apiRegister(email, password, displayName);
      const { user, accessToken } = handleAuthResponse(data);
      setState({ user, accessToken, isLoading: false });
    },
    [],
  );

  const logout = useCallback(() => {
    clearTokens();
    setState({ user: null, accessToken: null, isLoading: false });
  }, []);

  const value = useMemo(
    () => ({ ...state, login, register, logout }),
    [state, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
