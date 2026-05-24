import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";

async function startPracticeFromUI(page: Page, seed: SeedPracticeWorkflowData) {
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

async function answerAllPracticeQuestions(page: Page) {
  const questionCards = page.getByTestId("practice-question-card");
  await expect(questionCards).toHaveCount(5, { timeout: 15_000 });

  await expect(page.getByText(/Correct answer/i)).toHaveCount(0);
  await expect(page.getByText(/Marks awarded/i)).toHaveCount(0);
  await expect(page.getByText(/E2E explanation/i)).toHaveCount(0);

  for (let index = 0; index < 5; index += 1) {
    await questionCards.nth(index).getByTestId("practice-option-radio").first().check();
  }

  await expect(page.getByText("Progress: 5 / 5")).toBeVisible();
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

test.describe("student practice flow", () => {
  test("student starts practice, submits answers, reviews result, and sees analytics", async ({
    page,
    request
  }) => {
    test.setTimeout(150_000);

    const seed = await seedPracticeWorkflowData(request);

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );

    await startPracticeFromUI(page, seed);
    await expect(
      page.getByRole("heading", { name: `${seed.names.subject} Practice` })
    ).toBeVisible();

    await answerAllPracticeQuestions(page);
    await submitPractice(page);

    await expect(page.getByTestId("practice-result-summary")).toBeVisible();
    await expect(page.getByText("Correction Review")).toBeVisible();
    await expect(page.getByTestId("practice-correction-card")).toHaveCount(5);
    await expect(page.getByText(/Score/i).first()).toBeVisible();
    await expect(page.getByText(/Percentage/i).first()).toBeVisible();
    await expect(page.getByText(/Correct answer/i).first()).toBeVisible();
    await expect(page.getByText(/E2E explanation/i).first()).toBeVisible();

    await page.goto("/student/practice/analytics");
    await expect(
      page.getByRole("heading", { name: /^Practice Analytics$/i })
    ).toBeVisible();
    await expect(page.getByTestId("practice-analytics-dashboard")).toBeVisible();
    await expect(page.getByText("Recent Practice")).toBeVisible();
    await expect(page.getByTestId("practice-recent-sessions")).toContainText(
      seed.names.subject
    );
    await expect(page.getByTestId("practice-recent-sessions")).toContainText(
      seed.names.topic
    );
  });
});
