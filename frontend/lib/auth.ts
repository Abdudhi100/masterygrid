import { api, tokenStorage } from "@/lib/api";
import { dashboardPathForRole } from "@/lib/routes";
import type { CurrentUser, LoginCredentials, TokenPair, UserRole } from "@/types/auth";

export async function login(credentials: LoginCredentials) {
  const tokens = await api.post<TokenPair>("/auth/token/", credentials, {
    skipAuth: true
  });
  tokenStorage.setTokens(tokens.access, tokens.refresh);
  return getCurrentUser();
}

export function logout() {
  tokenStorage.clearTokens();
}

export async function getCurrentUser() {
  return api.get<CurrentUser>("/auth/me/");
}

export function isAdminRole(role: UserRole) {
  return role === "school_admin" || role === "platform_admin";
}

export function redirectPathForUser(user: CurrentUser) {
  return dashboardPathForRole(user.role);
}

export function isRoleAllowed(role: UserRole, allowedRoles: UserRole[]) {
  return allowedRoles.includes(role);
}
