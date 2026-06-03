import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import { seedPracticeWorkflowData } from "../utils/seed";

async function openSetupWizard(page: Page) {
  await page.goto("/admin/setup");
  await expect(page.getByTestId("school-setup-page")).toBeVisible({
    timeout: 15_000
  });
  await expect(
    page.getByRole("heading", { name: /^Setup Wizard$/i })
  ).toBeVisible();
  await expect(page.getByTestId("school-setup-progress")).toBeVisible();
  await expect(page.getByTestId("school-setup-next-step")).toBeVisible();
  await expect(page.getByTestId("school-setup-step")).toHaveCount(11);
}

function setupStep(page: Page, label: string) {
  return page.getByTestId("school-setup-step").filter({
    has: page.locator("h2").filter({ hasText: new RegExp(`^${label}$`, "i") })
  });
}

async function completeStepCount(page: Page) {
  return page
    .getByTestId("school-setup-step-status")
    .filter({ hasText: /^complete$/i })
    .count();
}

async function expectStepComplete(page: Page, label: string) {
  const step = setupStep(page, label);
  await expect(step).toBeVisible({ timeout: 15_000 });
  await expect(step.getByTestId("school-setup-step-status")).toHaveText(
    /^complete$/i
  );
}

test.describe("school setup wizard", () => {
  test("school admin reviews setup status, seeds workflow data, and follows an action link", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    await loginByApiAndStorage(
      page,
      request,
      credentials.admin.email,
      credentials.admin.password
    );

    await openSetupWizard(page);
    const beforeCompleteCount = await completeStepCount(page);
    await expect(page.locator("body")).toContainText(/complete|incomplete/i);

    await seedPracticeWorkflowData(request);

    await openSetupWizard(page);
    const afterCompleteCount = await completeStepCount(page);
    expect(afterCompleteCount).toBeGreaterThanOrEqual(beforeCompleteCount);

    await expectStepComplete(page, "Class levels");
    await expectStepComplete(page, "Class arms");
    await expectStepComplete(page, "Subjects");
    await expectStepComplete(page, "Topics");
    await expectStepComplete(page, "Teachers");
    await expectStepComplete(page, "Students");
    await expectStepComplete(page, "Teacher assignments");
    await expectStepComplete(page, "Student enrollments");
    await expectStepComplete(page, "Question bank");

    await page.getByTestId("school-setup-action-link").first().click();
    await expect
      .poll(
        async () => new URL(page.url()).pathname,
        { timeout: 15_000, message: "Waiting for setup action navigation" }
      )
      .not.toBe("/admin/setup");
  });
});
