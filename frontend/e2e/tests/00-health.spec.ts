import { expect, test } from "@playwright/test";

import { backendApiUrl } from "../utils/env";

test("backend health and frontend login shell are reachable", async ({
  page,
  request
}) => {
  const response = await request.get(`${backendApiUrl}/health/`);
  expect(response.ok()).toBeTruthy();

  const payload = await response.json();
  expect(payload.status).toBe("ok");
  expect(payload.database).toBe("ok");
  expect(payload.environment).toBeDefined();
  expect(payload.timestamp).toBeDefined();

  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: /sign in to your workspace/i })
  ).toBeVisible();
});
