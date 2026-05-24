import {
  request as playwrightRequest,
  type APIRequest,
  type APIRequestContext
} from "@playwright/test";

import { backendApiUrl } from "./env";

export type TokenPair = {
  access: string;
  refresh: string;
};

export class E2EApiError extends Error {
  constructor(
    public readonly path: string,
    public readonly status: number,
    public readonly body: string
  ) {
    super(`API request failed for ${path} with ${status}: ${body}`);
  }
}

export function getApiBaseUrl() {
  return backendApiUrl;
}

function apiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.replace(/^\/+/, "");
  return `${backendApiUrl}/${normalizedPath}`;
}

async function responseBody(response: { text: () => Promise<string> }) {
  const text = await response.text();
  if (!text) {
    return "";
  }

  try {
    return JSON.stringify(JSON.parse(text));
  } catch {
    return text;
  }
}

async function ensureOk(response: Awaited<ReturnType<APIRequestContext["get"]>>, path: string) {
  if (response.ok()) {
    return;
  }

  throw new E2EApiError(path, response.status(), await responseBody(response));
}

export async function createApiContext(apiRequest: APIRequest = playwrightRequest) {
  return apiRequest.newContext({
    baseURL: `${backendApiUrl}/`,
    extraHTTPHeaders: {
      Accept: "application/json"
    }
  });
}

export async function loginApi(
  request: APIRequestContext,
  email: string,
  password: string
) {
  const response = await request.post(apiUrl("auth/token/"), {
    data: { email, password }
  });

  if (!response.ok()) {
    throw new Error(
      `API login failed with ${response.status()}: ${await response.text()}`
    );
  }

  return (await response.json()) as TokenPair;
}

export function authHeaders(accessToken: string) {
  return {
    Authorization: `Bearer ${accessToken}`
  };
}

export function uniqueRunId(prefix = "e2e") {
  const random = Math.random().toString(36).slice(2, 8);
  return `${prefix}-${Date.now()}-${random}`;
}

export async function apiGet<T>(
  request: APIRequestContext,
  path: string,
  token: string
) {
  const response = await request.get(apiUrl(path), {
    headers: authHeaders(token)
  });
  await ensureOk(response, path);
  return (await response.json()) as T;
}

export async function apiPost<T>(
  request: APIRequestContext,
  path: string,
  token: string,
  data: unknown = {}
) {
  const response = await request.post(apiUrl(path), {
    headers: authHeaders(token),
    data
  });
  await ensureOk(response, path);
  return (await response.json()) as T;
}

export async function apiPatch<T>(
  request: APIRequestContext,
  path: string,
  token: string,
  data: unknown
) {
  const response = await request.patch(apiUrl(path), {
    headers: authHeaders(token),
    data
  });
  await ensureOk(response, path);
  return (await response.json()) as T;
}

export async function apiDelete(
  request: APIRequestContext,
  path: string,
  token: string
) {
  const response = await request.delete(apiUrl(path), {
    headers: authHeaders(token)
  });
  await ensureOk(response, path);
}
