import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";

async function submitLowScoreAssignment(
  page: Page,
  seed: SeedPracticeWorkflowData
) {
  await page.goto(`/student/assignments/${seed.ids.assignment}`);
  await expect(page.getByRole("heading")).toContainText("E2E Practice Assignment");

  await page.getByTestId("assignment-start-button").click();
  await page.waitForURL(/\/student\/assignments\/\d+\/attempt\?submissionId=\d+$/, {
    timeout: 15_000
  });

  const questionCards = page.getByTestId("assignment-question-card");
  await expect(questionCards).toHaveCount(5, { timeout: 15_000 });
  await expect(page.getByText(/Correct answer/i)).toHaveCount(0);
  await expect(page.getByText(/E2E explanation/i)).toHaveCount(0);

  for (let index = 0; index < 5; index += 1) {
    const wrongOptionIndex = index === 3 ? 1 : 0;
    await questionCards
      .nth(index)
      .getByTestId("assignment-option-radio")
      .nth(wrongOptionIndex)
      .check();
  }
  await expect(page.getByText("Progress: 5 / 5")).toBeVisible();

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toMatch(/submit/i);
    await dialog.accept();
  });
  await page.getByTestId("assignment-submit-button").click();
  await page.waitForURL(/\/student\/assignments\/\d+\/result\?submissionId=\d+$/, {
    timeout: 15_000
  });
  await expect(page.getByTestId("assignment-result-summary")).toBeVisible();
}

async function expectAdminInterventionSignals(page: Page, seed: SeedPracticeWorkflowData) {
  await page.goto("/admin/interventions");
  await expect(
    page.getByRole("heading", { name: /^Interventions$/i })
  ).toBeVisible();
  await expect(page.getByTestId("admin-intervention-dashboard")).toBeVisible();
  await expect(page.getByTestId("admin-intervention-summary")).toContainText(
    /Risk score/i
  );

  await expect(
    page.getByTestId("class-intervention-card").filter({
      hasText: seed.names.classArm
    })
  ).toBeVisible({ timeout: 15_000 });
  await expect(
    page.getByTestId("subject-intervention-card").filter({
      hasText: seed.names.subject
    })
  ).toBeVisible();
  await expect(
    page.getByTestId("teacher-intervention-card").filter({
      hasText: seed.teacherCredentials.email
    })
  ).toBeVisible();
  const weakCluster = page.getByTestId("weak-student-cluster-card").filter({
    hasText: seed.names.topic
  });
  await expect(weakCluster).toBeVisible();

  await weakCluster.getByTestId("intervention-action-link").click();
  await page.waitForURL(/\/admin\/analytics\/weak-students/, {
    timeout: 15_000
  });
  await expect(
    page.getByRole("heading", { name: /weak students/i })
  ).toBeVisible();
}

test.describe("school admin intervention dashboard", () => {
  test("admin sees intervention recommendations and can navigate to analytics", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );
    await submitLowScoreAssignment(page, seed);

    await loginByApiAndStorage(
      page,
      request,
      credentials.admin.email,
      credentials.admin.password
    );
    await expectAdminInterventionSignals(page, seed);
  });
});
