import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";

async function startLowScorePractice(page: Page, seed: SeedPracticeWorkflowData) {
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
}

async function answerVisiblePracticeQuestions(page: Page) {
  const questionCards = page.getByTestId("practice-question-card");
  await expect
    .poll(async () => questionCards.count(), { timeout: 15_000 })
    .toBeGreaterThan(0);
  const questionCount = await questionCards.count();

  await expect(page.getByText(/Correct answer/i)).toHaveCount(0);
  await expect(page.getByText(/E2E explanation/i)).toHaveCount(0);

  for (let index = 0; index < questionCount; index += 1) {
    await questionCards.nth(index).getByTestId("practice-option-radio").first().check();
  }

  await expect(page.getByText(`Progress: ${questionCount} / ${questionCount}`)).toBeVisible();
  return questionCount;
}

async function submitPractice(page: Page) {
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toMatch(/submit/i);
    await dialog.accept();
  });

  await page.getByTestId("practice-submit-button").click();
  await page.waitForURL(/\/student\/practice\/\d+\/result$/, {
    timeout: 15_000
  });
}

test.describe("student learning path flow", () => {
  test("student follows a recommended learning path into practice", async ({
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

    await startLowScorePractice(page, seed);
    await answerVisiblePracticeQuestions(page);
    await submitPractice(page);
    await expect(page.getByTestId("practice-result-summary")).toBeVisible();

    await page.goto("/student/learning-path");
    await expect(
      page.getByRole("heading", { name: /^Learning Path$/i })
    ).toBeVisible();
    await expect(page.getByTestId("learning-path-dashboard")).toBeVisible();
    await expect(page.getByTestId("learning-path-card").first()).toContainText(
      seed.names.topic
    );
    await expect(page.getByText("Weak Topic").first()).toBeVisible();

    await page.getByTestId("learning-path-primary-start-button").click();
    await page.waitForURL(/\/student\/practice\?.+/, { timeout: 15_000 });

    await expect(page.getByTestId("practice-subject-select")).toHaveValue(
      String(seed.ids.subject),
      { timeout: 15_000 }
    );
    await expect(page.getByTestId("practice-class-level-select")).toHaveValue(
      String(seed.ids.classLevel)
    );
    await expect(page.getByTestId("practice-topic-select")).toHaveValue(
      String(seed.ids.topic)
    );

    await page.getByTestId("practice-start-button").click();
    await page.waitForURL(/\/student\/practice\/\d+$/, { timeout: 15_000 });
    await expect(
      page.getByRole("heading", { name: `${seed.names.subject} Practice` })
    ).toBeVisible();

    const recommendedQuestionCount = await answerVisiblePracticeQuestions(page);
    expect(recommendedQuestionCount).toBeGreaterThan(0);
    await submitPractice(page);

    await expect(page.getByTestId("practice-result-summary")).toBeVisible();
    await expect(page.getByText("Correction Review")).toBeVisible();
    await expect(page.getByTestId("practice-correction-card")).toHaveCount(
      recommendedQuestionCount
    );
  });
});
