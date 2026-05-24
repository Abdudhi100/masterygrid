import { expect, test } from "@playwright/test";

import {
  clearAuthState,
  expectDashboardForRole,
  login
} from "../utils/auth";
import { credentials } from "../utils/env";

test.describe("authentication smoke", () => {
  test.beforeEach(async ({ page }) => {
    await clearAuthState(page);
  });

  test("admin can log in and reach the admin dashboard", async ({ page }) => {
    await login(page, credentials.admin.email, credentials.admin.password);
    await expectDashboardForRole(page, "admin");
  });

  test("teacher can log in and reach the teacher dashboard", async ({ page }) => {
    await login(page, credentials.teacher.email, credentials.teacher.password);
    await expectDashboardForRole(page, "teacher");
  });

  test("student can log in and reach the student dashboard", async ({ page }) => {
    await login(page, credentials.student.email, credentials.student.password);
    await expectDashboardForRole(page, "student");
  });

  test("wrong password shows an error and stays on login", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email address").fill(credentials.admin.email);
    await page.getByLabel("Password").fill("DefinitelyWrongPassword123!");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page).toHaveURL(/\/login$/);
    await expect(
      page.getByText(/unable|invalid|credentials|no active|failed/i)
    ).toBeVisible();
    await expect(page).not.toHaveURL(/\/(admin|teacher|student)\/dashboard$/);
  });
});
