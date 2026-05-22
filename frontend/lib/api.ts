import { ACCESS_TOKEN_KEY, API_BASE_URL, REFRESH_TOKEN_KEY } from "@/lib/constants";
import type { ApiErrorPayload } from "@/types/common";

type RequestOptions = {
  headers?: HeadersInit;
  skipAuth?: boolean;
};

export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload | null;

  constructor(message: string, status: number, payload: ApiErrorPayload | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function tokenFromStorage(key: string) {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(key);
}

function setToken(key: string, value: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(key, value);
  }
}

function removeToken(key: string) {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(key);
  }
}

export const tokenStorage = {
  getAccessToken: () => tokenFromStorage(ACCESS_TOKEN_KEY),
  getRefreshToken: () => tokenFromStorage(REFRESH_TOKEN_KEY),
  setTokens: (access: string, refresh: string) => {
    setToken(ACCESS_TOKEN_KEY, access);
    setToken(REFRESH_TOKEN_KEY, refresh);
  },
  clearTokens: () => {
    removeToken(ACCESS_TOKEN_KEY);
    removeToken(REFRESH_TOKEN_KEY);
  }
};

function normalizePath(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type");
  if (!contentType?.includes("application/json")) {
    return null;
  }
  return response.json();
}

function errorMessage(payload: ApiErrorPayload | null, fallback: string) {
  if (!payload) {
    return fallback;
  }

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  const firstKey = Object.keys(payload)[0];
  const firstValue = firstKey ? payload[firstKey] : null;
  if (Array.isArray(firstValue)) {
    return `${firstKey}: ${firstValue.join(" ")}`;
  }
  if (typeof firstValue === "string") {
    return `${firstKey}: ${firstValue}`;
  }

  return fallback;
}

async function refreshAccessToken() {
  const refresh = tokenStorage.getRefreshToken();
  if (!refresh) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh })
  });

  if (!response.ok) {
    tokenStorage.clearTokens();
    return null;
  }

  const data = (await response.json()) as { access?: string; refresh?: string };
  if (!data.access) {
    return null;
  }

  tokenStorage.setTokens(data.access, data.refresh ?? refresh);
  return data.access;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options: RequestOptions = {},
  hasRetried = false
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const accessToken = tokenStorage.getAccessToken();
  if (accessToken && !options.skipAuth) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${normalizePath(path)}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body)
  });

  if (response.status === 401 && !options.skipAuth && !hasRetried) {
    const refreshedToken = await refreshAccessToken();
    if (refreshedToken) {
      return request<T>(method, path, body, options, true);
    }
  }

  const payload = (await parseResponse(response)) as ApiErrorPayload | T | null;

  if (!response.ok) {
    throw new ApiError(
      errorMessage(payload as ApiErrorPayload | null, "Request failed."),
      response.status,
      payload as ApiErrorPayload | null
    );
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>("GET", path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, body, options),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PATCH", path, body, options),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>("DELETE", path, undefined, options)
};
