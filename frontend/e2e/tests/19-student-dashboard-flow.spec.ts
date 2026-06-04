import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";

async function openStudentAssignment(page: Page, assignmentTitle: string) {
  await page.goto("/student/assignments");
  await expect(
    page.getByRole("heading", { name: /^My Assignments$/i })
  ).toBeVisible();

  const assignmentCard = page
    .getByTestId("student-assignment-card")
    .filter({ hasText: assignmentTitle });
  await expect(assignmentCard).toBeVisible({ timeout: 15_000 });
  await assignmentCard.getByRole("link", { name: /^View Details$/i }).click();
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();
}

async function submitSeededAssignment(page: Page, assignmentTitle: string) {
  await openStudentAssignment(page, assignmentTitle);
  await expect(page.getByTestId("assignment-start-button")).toBeVisible({
    timeout: 15_000
  });
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

async function completeLowScorePractice(page: Page, seed: SeedPracticeWorkflowData) {
  await page.goto("/student/practice");
  await expect(page.getByRole("heading", { name: /^Practice$/i })).toBeVisible();

  const subjectSelect = page.getByTestId("practice-subject-select");
  await expectSelectHasOption(
    subjectSelect,
    seed.names.subject,
    `student dashboard practice subject select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await subjectSelect.selectOption({ label: seed.names.subject });

  const classLevelSelect = page.getByTestId("practice-class-level-select");
  await expectSelectHasOption(
    classLevelSelect,
    seed.names.classLevel,
    `student dashboard practice class level select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await classLevelSelect.selectOption({ label: seed.names.classLevel });

  const topicSelect = page.getByTestId("practice-topic-select");
  await expectSelectHasOption(
    topicSelect,
    seed.names.topic,
    `student dashboard practice topic select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await topicSelect.selectOption({ label: seed.names.topic });

  await page.getByTestId("practice-difficulty-select").selectOption("mixed");
  await page.getByTestId("practice-question-count-input").fill("5");
  await page.getByTestId("practice-start-button").click();
  await page.waitForURL(/\/student\/practice\/\d+$/, { timeout: 15_000 });

  const questionCards = page.getByTestId("practice-question-card");
  await expect(questionCards).toHaveCount(5, { timeout: 15_000 });
  for (let index = 0; index < 5; index += 1) {
    await questionCards.nth(index).getByTestId("practice-option-radio").first().check();
  }

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toMatch(/submit/i);
    await dialog.accept();
  });
  await page.getByTestId("practice-submit-button").click();
  await page.waitForURL(/\/student\/practice\/\d+\/result$/, {
    timeout: 15_000
  });
  await expect(page.getByTestId("practice-result-summary")).toBeVisible();
}

test.describe("student dashboard flow", () => {
  test("student sees a useful learning home with assignments, practice, recommendations, and quick actions", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const assignmentTitle = `E2E Practice Assignment ${seed.runId}`;

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );
    await submitSeededAssignment(page, assignmentTitle);
    await completeLowScorePractice(page, seed);

    await page.goto("/student/dashboard");
    await expect(
      page.getByRole("heading", { name: /student dashboard/i })
    ).toBeVisible();
    await expect(page.getByTestId("student-dashboard-page")).toBeVisible();
    await expect(page.getByTestId("student-dashboard-summary")).toContainText(
      "Assignment average"
    );
    await expect(page.getByTestId("student-dashboard-summary")).toContainText(
      "Practice average"
    );

    await expect(
      page.getByTestId("student-dashboard-urgent-assignments")
    ).toBeVisible();
    await expect(page.getByTestId("student-dashboard-learning-path")).toContainText(
      seed.names.topic
    );
    await expect(
      page.getByTestId("student-dashboard-practice-summary")
    ).toBeVisible();
    await expect(page.getByTestId("student-dashboard-notifications")).toContainText(
      "New assignment published"
    );
    await expect(page.getByText("Recent Results")).toBeVisible();
    await expect(page.getByText(assignmentTitle, { exact: true }).first()).toBeVisible();

    const learningPathAction = page
      .getByTestId("student-dashboard-quick-action")
      .filter({ hasText: "Open learning path" });
    await expect(learningPathAction).toBeVisible();
    await learningPathAction.click();
    await page.waitForURL(/\/student\/learning-path$/, { timeout: 15_000 });
    await expect(page.getByTestId("learning-path-dashboard")).toBeVisible();
  });
});
