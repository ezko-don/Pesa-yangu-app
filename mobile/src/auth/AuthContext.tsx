import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { api, clearTokens, getAccess, saveTokens } from "../api/client";
import type { AuthTokens, User } from "../api/types";

interface RegisterInput {
  email: string;
  password: string;
  first_name?: string;
  account_type?: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (input: RegisterInput) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      const me = await api.get<User>("/api/auth/me/");
      setUser(me);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      const token = await getAccess();
      if (token) await loadUser();
      setLoading(false);
    })();
  }, [loadUser]);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const tokens = await api.post<AuthTokens>(
        "/api/auth/login/",
        { email, password },
        false
      );
      await saveTokens(tokens);
      await loadUser();
    },
    [loadUser]
  );

  const signUp = useCallback(async (input: RegisterInput) => {
    const res = await api.post<{ user: User; tokens: AuthTokens }>(
      "/api/auth/register/",
      input,
      false
    );
    await saveTokens(res.tokens);
    setUser(res.user);
  }, []);

  const signOut = useCallback(async () => {
    await clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut, refreshUser: loadUser }),
    [user, loading, signIn, signUp, signOut, loadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
