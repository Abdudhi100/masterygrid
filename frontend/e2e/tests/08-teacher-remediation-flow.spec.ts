import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";

function assignmentIdFromUrl(url: string) {
  const match = url.match(/\/teacher\/assignments\/(\d+)$/);
  if (!match) {
    throw new Error(`Unable to read assignment id from URL: ${url}`);
  }
  return Number(match[1]);
}

async function submitLowScoreSeedAssignment(
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
    await questionCards.nth(index).getByTestId("assignment-option-radio").first().check();
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

async function openRemediationAndPrefillAssignment(
  page: Page,
  seed: SeedPracticeWorkflowData
) {
  await page.goto("/teacher/remediation");
  await expect(
    page.getByRole("heading", { name: /^Remediation$/i })
  ).toBeVisible();
  await expect(page.getByTestId("teacher-remediation-page")).toBeVisible();

  const card = page.getByTestId("remediation-topic-card").filter({
    hasText: seed.names.topic
  });
  await expect(card).toBeVisible({ timeout: 15_000 });
  await expect(card).toContainText(seed.names.subject);
  await expect(card).toContainText(seed.names.classArm);
  await expect(card).toContainText(/approved questions/i);

  await card.getByTestId("remediation-create-assignment-button").click();
  await page.waitForURL(/\/teacher\/assignments\/new\?.*remedial=true/, {
    timeout: 15_000
  });

  await expect(page.getByTestId("assignment-remedial-badge")).toBeVisible();
  await expect(page.getByTestId("assignment-class-arm-select")).toHaveValue(
    String(seed.ids.classArm),
    { timeout: 15_000 }
  );
  await expect(page.getByTestId("assignment-subject-select")).toHaveValue(
    String(seed.ids.subject)
  );
  await expect(page.getByTestId("assignment-topic-select")).toHaveValue(
    String(seed.ids.topic),
    { timeout: 15_000 }
  );
  await expect(page.getByTestId("assignment-question-count-input")).toHaveValue(
    "5"
  );
  await expect(page.getByTestId("assignment-title-input")).toHaveValue(
    `Remedial: ${seed.names.topic}`
  );
}

async function generateAndPublishRemedialAssignment(page: Page) {
  await page.getByTestId("assignment-generate-button").click();
  await expect(page.getByTestId("assignment-draft-preview")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("assignment-draft-preview")).toContainText(
    "5 selected questions"
  );
  await expect(page.getByTestId("assignment-status-badge")).toContainText(
    /draft/i
  );

  await page.getByTestId("assignment-publish-button").click();
  await page.waitForURL(/\/teacher\/assignments\/\d+$/, { timeout: 15_000 });
  const assignmentId = assignmentIdFromUrl(page.url());
  await expect(page.getByRole("heading", { name: /Remedial:/i })).toBeVisible();
  await expect(page.getByTestId("assignment-status-badge")).toContainText(
    /published/i
  );
  expect(assignmentId).toBeGreaterThan(0);
}

test.describe("teacher remediation flow", () => {
  test("teacher creates a remedial assignment from weak topic recommendations", async ({
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
    await submitLowScoreSeedAssignment(page, seed);

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await openRemediationAndPrefillAssignment(page, seed);
    await generateAndPublishRemedialAssignment(page);
  });
});
