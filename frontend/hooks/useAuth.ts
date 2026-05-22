"use client";

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import { usePathname, useRouter } from "next/navigation";

import {
  getCurrentUser,
  isRoleAllowed,
  login as loginRequest,
  logout as logoutRequest,
  redirectPathForUser
} from "@/lib/auth";
import { tokenStorage } from "@/lib/api";
import type { CurrentUser, LoginCredentials, UserRole } from "@/types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  user: CurrentUser | null;
  status: AuthStatus;
  login: (credentials: LoginCredentials) => Promise<CurrentUser>;
  logout: () => void;
  refreshUser: () => Promise<CurrentUser | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refreshUser = useCallback(async () => {
    if (!tokenStorage.getAccessToken()) {
      setUser(null);
      setStatus("unauthenticated");
      return null;
    }

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setStatus("authenticated");
      return currentUser;
    } catch {
      logoutRequest();
      setUser(null);
      setStatus("unauthenticated");
      return null;
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setStatus("loading");
    const currentUser = await loginRequest(credentials);
    setUser(currentUser);
    setStatus("authenticated");
    return currentUser;
  }, []);

  const logout = useCallback(() => {
    logoutRequest();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({ user, status, login, logout, refreshUser }),
    [user, status, login, logout, refreshUser]
  );

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}

export function useRequireAuth(allowedRoles: UserRole[]) {
  const { user, status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "loading") {
      return;
    }

    if (status === "unauthenticated") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    if (user && !isRoleAllowed(user.role, allowedRoles)) {
      router.replace(redirectPathForUser(user));
    }
  }, [allowedRoles, pathname, router, status, user]);

  return {
    user,
    status,
    isAuthorized:
      status === "authenticated" && user
        ? isRoleAllowed(user.role, allowedRoles)
        : false
  };
}
