import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";

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
  for (let index = 0; index < 5; index += 1) {
    const wrongOptionIndex = index === 3 ? 1 : 0;
    await questionCards
      .nth(index)
      .getByTestId("assignment-option-radio")
      .nth(wrongOptionIndex)
      .check();
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

async function completePracticeSession(page: Page, seed: SeedPracticeWorkflowData) {
  await page.goto("/student/practice");
  await expect(page.getByRole("heading", { name: /^Practice$/i })).toBeVisible();

  const subjectSelect = page.getByTestId("practice-subject-select");
  await expectSelectHasOption(
    subjectSelect,
    seed.names.subject,
    `subject select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await subjectSelect.selectOption({ label: seed.names.subject });

  const classLevelSelect = page.getByTestId("practice-class-level-select");
  await expectSelectHasOption(
    classLevelSelect,
    seed.names.classLevel,
    `class level select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await classLevelSelect.selectOption({ label: seed.names.classLevel });

  const topicSelect = page.getByTestId("practice-topic-select");
  await expectSelectHasOption(
    topicSelect,
    seed.names.topic,
    `topic select for seed IDs ${JSON.stringify(seed.ids)}`
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

async function expectPrintView(page: Page, seed: SeedPracticeWorkflowData) {
  await expect(page.getByTestId("student-progress-print-page")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByText("Student Progress Report")).toBeVisible();
  await expect(page.getByText(seed.studentCredentials.email)).toBeVisible();
  await expect(page.getByTestId("student-progress-print-summary")).toContainText(
    /Overall average/i
  );
  await expect(page.getByTestId("student-progress-print-recommendations")).toContainText(
    /targeted practice|remedial assignment|missed assignments/i
  );
  await expect(page.getByTestId("student-progress-print-button")).toBeVisible();
}

test.describe("student progress report print view", () => {
  test("admin and teacher can open printable student progress reports", async ({
    page,
    request
  }) => {
    test.setTimeout(210_000);

    const seed = await seedPracticeWorkflowData(request);

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );
    await submitLowScoreAssignment(page, seed);
    await completePracticeSession(page, seed);

    await loginByApiAndStorage(
      page,
      request,
      credentials.admin.email,
      credentials.admin.password
    );
    await page.goto(`/admin/students/${seed.ids.student}/progress-report`);
    await expect(page.getByTestId("student-progress-report-page")).toBeVisible({
      timeout: 15_000
    });
    await page.getByTestId("student-progress-print-link").click();
    await page.waitForURL(
      new RegExp(`/admin/students/${seed.ids.student}/progress-report/print$`),
      { timeout: 15_000 }
    );
    await expectPrintView(page, seed);

    await page.getByTestId("student-progress-print-back-link").click();
    await page.waitForURL(
      new RegExp(`/admin/students/${seed.ids.student}/progress-report$`),
      { timeout: 15_000 }
    );
    await expect(page.getByTestId("student-progress-report-page")).toBeVisible();

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await page.goto(`/teacher/students/${seed.ids.student}/progress-report/print`);
    await expectPrintView(page, seed);
  });
});
