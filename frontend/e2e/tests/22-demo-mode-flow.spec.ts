import { expect, test } from "@playwright/test";

import { clearAuthState, expectDashboardForRole } from "../utils/auth";

const demoModeEnabled = process.env.NEXT_PUBLIC_ENABLE_DEMO_MODE === "true";

test.describe("demo mode login", () => {
  test.skip(
    !demoModeEnabled,
    "Set NEXT_PUBLIC_ENABLE_DEMO_MODE=true for the frontend and Playwright process to run this spec."
  );

  test.beforeEach(async ({ page }) => {
    await clearAuthState(page);
  });

  test("student demo account can prefill credentials and sign in", async ({
    page
  }) => {
    const panel = page.getByTestId("demo-login-panel");
    await expect(panel).toBeVisible();

    await page.getByTestId("demo-login-student1").click();

    await expect(page.getByLabel("Email address")).toHaveValue(
      "student1@masterygrid.demo"
    );
    await expect(page.getByLabel("Password")).toHaveValue("Password123!");

    await page.getByRole("button", { name: /^sign in$/i }).click();
    await expectDashboardForRole(page, "student");
  });
});
