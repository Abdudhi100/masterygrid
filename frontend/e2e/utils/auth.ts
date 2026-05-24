import fs from "node:fs";
import path from "node:path";

import {
  expect,
  type APIRequestContext,
  type ConsoleMessage,
  type Page,
  type Request,
  type Response
} from "@playwright/test";

import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY
} from "../../lib/constants";
import { apiGet, loginApi } from "./api";
import type { E2ERole } from "./env";

type AuthDebugState = {
  consoleErrors: string[];
  pageErrors: string[];
  failedRequests: string[];
  apiRequests: string[];
  apiResponses: string[];
  tokenResponse?: {
    url: string;
    status: number;
    body: string;
  };
  meResponse?: {
    url: string;
    status: number;
    body: string;
  };
};

type ResponseWaitResult = {
  response: Response | null;
  error: string;
};

type CurrentUser = {
  role: string;
};

const dashboardRoutes: Record<E2ERole, RegExp> = {
  admin: /\/admin\/dashboard$/,
  teacher: /\/teacher\/dashboard$/,
  student: /\/student\/dashboard$/
};

const dashboardPaths: Record<E2ERole, string> = {
  admin: "/admin/dashboard",
  teacher: "/teacher/dashboard",
  student: "/student/dashboard"
};

const dashboardHeadings: Record<E2ERole, RegExp> = {
  admin: /school dashboard/i,
  teacher: /teacher dashboard/i,
  student: /student dashboard/i
};

function isTokenResponse(url: string) {
  return /\/api\/auth\/token\/?$/.test(url);
}

function isMeResponse(url: string) {
  return /\/api\/auth\/me\/?$/.test(url);
}

function isUsefulNetworkUrl(url: string) {
  return url.includes("/api/") || url.includes("/auth");
}

function truncate(value: string, maxLength = 2500) {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength)}... [truncated ${value.length - maxLength} chars]`;
}

function roleFromUserRole(role: string): E2ERole {
  if (role === "teacher") {
    return "teacher";
  }

  if (role === "student") {
    return "student";
  }

  return "admin";
}

function startAuthDebugCapture(page: Page) {
  const state: AuthDebugState = {
    consoleErrors: [],
    pageErrors: [],
    failedRequests: [],
    apiRequests: [],
    apiResponses: []
  };

  const onConsole = (message: ConsoleMessage) => {
    if (message.type() === "error") {
      state.consoleErrors.push(
        `${message.type()}: ${message.text()} (${message.location().url}:${
          message.location().lineNumber
        })`
      );
    }
  };

  const onPageError = (error: Error) => {
    state.pageErrors.push(error.stack ?? error.message);
  };

  const onRequest = (request: Request) => {
    if (isUsefulNetworkUrl(request.url())) {
      state.apiRequests.push(`${request.method()} ${request.url()}`);
    }
  };

  const onResponse = (response: Response) => {
    if (isUsefulNetworkUrl(response.url())) {
      state.apiResponses.push(`${response.status()} ${response.url()}`);
    }
  };

  const onRequestFailed = (request: Request) => {
    const failure = request.failure();
    state.failedRequests.push(
      `${request.method()} ${request.url()} :: ${failure?.errorText ?? "unknown failure"}`
    );
  };

  page.on("console", onConsole);
  page.on("pageerror", onPageError);
  page.on("request", onRequest);
  page.on("response", onResponse);
  page.on("requestfailed", onRequestFailed);

  return {
    state,
    stop: () => {
      page.off("console", onConsole);
      page.off("pageerror", onPageError);
      page.off("request", onRequest);
      page.off("response", onResponse);
      page.off("requestfailed", onRequestFailed);
    }
  };
}

async function safeResponseText(response: Response) {
  try {
    return truncate(await response.text());
  } catch (error) {
    return `Unable to read response body: ${
      error instanceof Error ? error.message : String(error)
    }`;
  }
}

async function safeBodyText(page: Page) {
  try {
    return truncate(await page.locator("body").innerText());
  } catch {
    return "Unable to read body text.";
  }
}

async function safeVisibleErrorText(page: Page) {
  const locators = [
    page.locator('[role="alert"], .text-danger, .text-red-600, .text-red-700'),
    page.getByText(/unable|invalid|credentials|failed|error/i)
  ];

  const allTexts: string[] = [];
  try {
    for (const locator of locators) {
      allTexts.push(...(await locator.allTextContents()));
    }
  } catch {
    return allTexts.map((text) => text.trim()).filter(Boolean).join("\n");
  }

  return allTexts.map((text) => text.trim()).filter(Boolean).join("\n");
}

async function authStorageSummary(page: Page) {
  try {
    return await page.evaluate(() => {
      const summary: Record<string, string> = {};

      for (let index = 0; index < window.localStorage.length; index += 1) {
        const key = window.localStorage.key(index);
        if (!key) {
          continue;
        }

        const lowerKey = key.toLowerCase();
        if (
          lowerKey.includes("token") ||
          lowerKey.includes("auth") ||
          lowerKey.includes("masterygrid")
        ) {
          const value = window.localStorage.getItem(key);
          summary[key] = value ? `[set: ${value.length} chars]` : "[empty]";
        }
      }

      return summary;
    });
  } catch {
    return {};
  }
}

async function expectedAuthStorageSummary(page: Page) {
  try {
    return await page.evaluate(
      ({ accessTokenKey, refreshTokenKey }) => ({
        expectedAccessTokenKey: accessTokenKey,
        expectedRefreshTokenKey: refreshTokenKey,
        accessToken: window.localStorage.getItem(accessTokenKey)
          ? "[set]"
          : "[missing]",
        refreshToken: window.localStorage.getItem(refreshTokenKey)
          ? "[set]"
          : "[missing]",
        allKeys: Object.keys(window.localStorage)
      }),
      {
        accessTokenKey: ACCESS_TOKEN_KEY,
        refreshTokenKey: REFRESH_TOKEN_KEY
      }
    );
  } catch {
    return {
      expectedAccessTokenKey: ACCESS_TOKEN_KEY,
      expectedRefreshTokenKey: REFRESH_TOKEN_KEY,
      accessToken: "[unreadable]",
      refreshToken: "[unreadable]",
      allKeys: []
    };
  }
}

async function captureScreenshot(page: Page, label: string) {
  try {
    const outputDir = path.join(process.cwd(), "test-results", "login-debug");
    fs.mkdirSync(outputDir, { recursive: true });
    const safeLabel = label.replace(/[^a-z0-9]+/gi, "-").slice(0, 80);
    const filename = `${Date.now()}-${safeLabel}.png`;
    const screenshotPath = path.join(outputDir, filename);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    return screenshotPath;
  } catch (error) {
    return `Unable to capture screenshot: ${
      error instanceof Error ? error.message : String(error)
    }`;
  }
}

async function buildAuthDebugMessage(
  page: Page,
  state: AuthDebugState,
  label: string
) {
  const screenshotPath = await captureScreenshot(page, label);
  const visibleErrorText = await safeVisibleErrorText(page);
  const bodyText = await safeBodyText(page);
  const storage = await authStorageSummary(page);

  return [
    `Auth debug: ${label}`,
    `Current URL: ${page.url()}`,
    `Visible login/error text: ${visibleErrorText || "None detected"}`,
    `Auth storage keys: ${JSON.stringify(storage, null, 2)}`,
    `Token response: ${JSON.stringify(state.tokenResponse ?? null, null, 2)}`,
    `Current user response: ${JSON.stringify(state.meResponse ?? null, null, 2)}`,
    `API requests:\n${state.apiRequests.join("\n") || "None captured"}`,
    `API responses:\n${state.apiResponses.join("\n") || "None captured"}`,
    `Failed requests:\n${state.failedRequests.join("\n") || "None captured"}`,
    `Console errors:\n${state.consoleErrors.join("\n") || "None captured"}`,
    `Page errors:\n${state.pageErrors.join("\n") || "None captured"}`,
    `Screenshot: ${screenshotPath}`,
    `Page text:\n${bodyText}`
  ].join("\n\n");
}

export async function clearAuthState(page: Page) {
  await page.goto("/login");
  await page.evaluate(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });
}

export async function login(page: Page, email: string, password: string) {
  await clearAuthState(page);

  const capture = startAuthDebugCapture(page);
  const { state } = capture;

  const tokenResponsePromise: Promise<ResponseWaitResult> = page
    .waitForResponse((response) => isTokenResponse(response.url()), {
      timeout: 15_000
    })
    .then((response) => ({ response, error: "" }))
    .catch((error) => ({
      response: null,
      error: error instanceof Error ? error.message : String(error)
    }));
  const meResponsePromise: Promise<ResponseWaitResult> = page
    .waitForResponse((response) => isMeResponse(response.url()), {
      timeout: 15_000
    })
    .then((response) => ({ response, error: "" }))
    .catch((error) => ({
      response: null,
      error: error instanceof Error ? error.message : String(error)
    }));

  try {
    const emailInput = page.getByLabel("Email address");
    const passwordInput = page.getByLabel("Password");
    const signInButton = page.getByRole("button", { name: /sign in/i });

    await expect(emailInput).toBeVisible({ timeout: 10_000 });
    await expect(passwordInput).toBeVisible();
    await expect(signInButton).toBeVisible();
    await expect(signInButton).toBeEnabled();

    await emailInput.fill(email);
    await passwordInput.fill(password);
    await signInButton.click();

    const tokenResult = await tokenResponsePromise;
    if (!tokenResult.response) {
      throw new Error(
        await buildAuthDebugMessage(
          page,
          state,
          `No token response captured for ${email}: ${tokenResult.error}`
        )
      );
    }
    const tokenResponse = tokenResult.response;

    state.tokenResponse = {
      url: tokenResponse.url(),
      status: tokenResponse.status(),
      body: await safeResponseText(tokenResponse)
    };

    if (!tokenResponse.ok()) {
      throw new Error(
        await buildAuthDebugMessage(
          page,
          state,
          `Token login failed for ${email}`
        )
      );
    }

    const meResult = await meResponsePromise;
    const meResponse = meResult.response;
    if (meResponse) {
      state.meResponse = {
        url: meResponse.url(),
        status: meResponse.status(),
        body: await safeResponseText(meResponse)
      };

      if (!meResponse.ok()) {
        throw new Error(
          await buildAuthDebugMessage(
            page,
            state,
            `Current user lookup failed after token login for ${email}`
          )
        );
      }
    }

    try {
      await page.waitForURL(/\/(admin|teacher|student)\/dashboard$/, {
        timeout: 15_000
      });
    } catch (error) {
      throw new Error(
        await buildAuthDebugMessage(
          page,
          state,
          `Dashboard redirect did not complete for ${email}: ${
            error instanceof Error ? error.message : String(error)
          }`
        )
      );
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (message.startsWith("Auth debug:")) {
      throw error;
    }

    throw new Error(
      await buildAuthDebugMessage(
        page,
        state,
        `Login helper failed for ${email}: ${message}`
      )
    );
  } finally {
    capture.stop();
  }
}

export async function loginAs(page: Page, email: string, password: string) {
  await login(page, email, password);
}

export async function loginByApiAndStorage(
  page: Page,
  request: APIRequestContext,
  email: string,
  password: string
) {
  const tokens = await loginApi(request, email, password);
  const currentUser = await apiGet<CurrentUser>(request, "auth/me/", tokens.access);
  const role = roleFromUserRole(currentUser.role);
  const dashboardPath = dashboardPaths[role];
  const capture = startAuthDebugCapture(page);
  const { state } = capture;
  const meResponsePromise: Promise<ResponseWaitResult> = page
    .waitForResponse((response) => isMeResponse(response.url()), {
      timeout: 15_000
    })
    .then((response) => ({ response, error: "" }))
    .catch((error) => ({
      response: null,
      error: error instanceof Error ? error.message : String(error)
    }));

  try {
    await page.addInitScript(
      ({ access, refresh, accessTokenKey, refreshTokenKey }) => {
        window.localStorage.clear();
        window.sessionStorage.clear();
        window.localStorage.setItem(accessTokenKey, access);
        window.localStorage.setItem(refreshTokenKey, refresh);
      },
      {
        access: tokens.access,
        refresh: tokens.refresh,
        accessTokenKey: ACCESS_TOKEN_KEY,
        refreshTokenKey: REFRESH_TOKEN_KEY
      }
    );

    await page.goto(dashboardPath, { waitUntil: "domcontentloaded" });

    if (
      /\/login(?:\?|$)/.test(
        new URL(page.url()).pathname + new URL(page.url()).search
      )
    ) {
      throw new Error(
        [
          "API-storage login redirected back to login.",
          `Current URL: ${page.url()}`,
          `Expected dashboard: ${dashboardPath}`,
          `Expected auth keys: ${ACCESS_TOKEN_KEY}, ${REFRESH_TOKEN_KEY}`,
          `Expected auth storage summary: ${JSON.stringify(
            await expectedAuthStorageSummary(page),
            null,
            2
          )}`,
          `Auth-related storage summary: ${JSON.stringify(
            await authStorageSummary(page),
            null,
            2
          )}`,
          `Page text:\n${await safeBodyText(page)}`
        ].join("\n\n")
      );
    }

    const meResult = await meResponsePromise;
    if (!meResult.response) {
      throw new Error(
        await buildAuthDebugMessage(
          page,
          state,
          `API-storage login did not observe browser /auth/me/ response: ${meResult.error}`
        )
      );
    }

    state.meResponse = {
      url: meResult.response.url(),
      status: meResult.response.status(),
      body: await safeResponseText(meResult.response)
    };

    if (!meResult.response.ok()) {
      throw new Error(
        await buildAuthDebugMessage(
          page,
          state,
          "API-storage login browser /auth/me/ response failed"
        )
      );
    }

    await expectDashboardForRole(page, role);
  } catch (error) {
    throw new Error(
      [
        "API-storage login reached a protected route but dashboard verification failed.",
        `Current URL: ${page.url()}`,
        `Expected dashboard: ${dashboardPath}`,
        `Expected auth keys: ${ACCESS_TOKEN_KEY}, ${REFRESH_TOKEN_KEY}`,
        `Expected auth storage summary: ${JSON.stringify(
          await expectedAuthStorageSummary(page),
          null,
          2
        )}`,
        `Page text:\n${await safeBodyText(page)}`,
        `Original error: ${error instanceof Error ? error.message : String(error)}`
      ].join("\n\n")
    );
  } finally {
    capture.stop();
  }

  return { currentUser, role, tokens };
}

export async function logout(page: Page) {
  await page.getByRole("button", { name: /sign out/i }).click();
  await expect(page).toHaveURL(/\/login$/);
}

export async function expectDashboardForRole(page: Page, role: E2ERole) {
  try {
    await page.waitForURL(dashboardRoutes[role], { timeout: 15_000 });
  } catch (error) {
    const message = [
      `Expected dashboard route: ${dashboardRoutes[role]}`,
      `Current URL: ${page.url()}`,
      `Page text:\n${await safeBodyText(page)}`,
      `Original error: ${error instanceof Error ? error.message : String(error)}`
    ].join("\n\n");
    throw new Error(message);
  }

  try {
    await expect(
      page.getByRole("heading", { name: dashboardHeadings[role] })
    ).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("button", { name: /sign out/i })).toBeVisible();
  } catch (error) {
    const message = [
      `Dashboard route loaded but expected shell did not render for role: ${role}`,
      `Current URL: ${page.url()}`,
      `Expected dashboard heading: ${dashboardHeadings[role]}`,
      `Page text:\n${await safeBodyText(page)}`,
      `Original error: ${error instanceof Error ? error.message : String(error)}`
    ].join("\n\n");
    throw new Error(message);
  }
}
