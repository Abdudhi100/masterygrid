import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";

function assignmentIdFromUrl(url: string) {
  const match = url.match(/\/teacher\/assignments\/(\d+)$/);
  if (!match) {
    throw new Error(`Unable to read assignment id from URL: ${url}`);
  }
  return Number(match[1]);
}

async function createAssignmentFromTeacherUI(
  page: Page,
  seed: SeedPracticeWorkflowData,
  assignmentTitle: string
) {
  await page.goto("/teacher/assignments/new");
  await expect(
    page.getByRole("heading", { name: /^Create Assignment$/i })
  ).toBeVisible();

  const classArmSelect = page.getByTestId("assignment-class-arm-select");
  await expectSelectHasOption(
    classArmSelect,
    seed.names.classArm,
    `teacher assignment class arm select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await classArmSelect.selectOption({ label: seed.names.classArm });

  const subjectSelect = page.getByTestId("assignment-subject-select");
  await expectSelectHasOption(
    subjectSelect,
    seed.names.subject,
    `teacher assignment subject select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await subjectSelect.selectOption({ label: seed.names.subject });

  const topicSelect = page.getByTestId("assignment-topic-select");
  await expectSelectHasOption(
    topicSelect,
    seed.names.topic,
    `teacher assignment topic select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await topicSelect.selectOption({ label: seed.names.topic });

  await page.getByTestId("assignment-title-input").fill(assignmentTitle);
  await page.getByTestId("assignment-question-count-input").fill("5");
  await page.getByTestId("assignment-generate-button").click();

  await expect(page.getByTestId("assignment-draft-preview")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("assignment-draft-preview")).toContainText(
    "Draft preview"
  );
  await expect(page.getByTestId("assignment-draft-preview")).toContainText(
    "5 selected questions"
  );
  await expect(page.getByTestId("assignment-status-badge")).toContainText(
    /draft/i
  );

  await page.getByTestId("assignment-publish-button").click();
  await page.waitForURL(/\/teacher\/assignments\/\d+$/, { timeout: 15_000 });

  const assignmentId = assignmentIdFromUrl(page.url());
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();
  await expect(page.getByTestId("assignment-status-badge")).toContainText(
    /published/i
  );

  return assignmentId;
}

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

async function answerAllAssignmentQuestions(page: Page) {
  const questionCards = page.getByTestId("assignment-question-card");
  await expect(questionCards).toHaveCount(5, { timeout: 15_000 });

  await expect(page.getByText(/Correct answer/i)).toHaveCount(0);
  await expect(page.getByText(/Marks awarded/i)).toHaveCount(0);
  await expect(page.getByText(/E2E explanation/i)).toHaveCount(0);

  for (let index = 0; index < 5; index += 1) {
    await questionCards.nth(index).getByTestId("assignment-option-radio").first().check();
  }

  await expect(page.getByText("Progress: 5 / 5")).toBeVisible();
}

async function submitAssignment(page: Page) {
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toMatch(/submit/i);
    await dialog.accept();
  });

  await page.getByTestId("assignment-submit-button").click();
  await page.waitForURL(/\/student\/assignments\/\d+\/result\?submissionId=\d+$/, {
    timeout: 15_000
  });
}

async function verifyTeacherResult(
  page: Page,
  assignmentId: number,
  expectedStudentName: string
) {
  await page.goto(`/teacher/assignments/${assignmentId}/results`);
  await expect(
    page.getByRole("heading", { name: /^Assignment Results$/i })
  ).toBeVisible();

  const resultsTable = page.getByTestId("teacher-assignment-results-table");
  await expect(resultsTable).toBeVisible({ timeout: 15_000 });
  await expect(resultsTable).toContainText(expectedStudentName);
  await expect(resultsTable).toContainText(/submitted|graded|auto submitted/i);
  await expect(resultsTable).toContainText(/[0-5]\/5/);
}

test.describe("teacher assignment flow", () => {
  test("teacher creates and publishes assignment, student submits, teacher sees results", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const assignmentTitle = `E2E Teacher UI Assignment ${seed.runId}`;
    const expectedStudentName = `E2E Student ${seed.runId}`;

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );

    const assignmentId = await createAssignmentFromTeacherUI(
      page,
      seed,
      assignmentTitle
    );

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );

    await openStudentAssignment(page, assignmentTitle);
    await page.getByTestId("assignment-start-button").click();
    await page.waitForURL(/\/student\/assignments\/\d+\/attempt\?submissionId=\d+$/, {
      timeout: 15_000
    });
    await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();

    await answerAllAssignmentQuestions(page);
    await submitAssignment(page);

    await expect(page.getByTestId("assignment-result-summary")).toBeVisible();
    await expect(page.getByText("Correction Review")).toBeVisible();
    await expect(page.getByTestId("assignment-correction-card")).toHaveCount(5);
    await expect(page.getByText(/Score/i).first()).toBeVisible();
    await expect(page.getByText(/Percentage/i).first()).toBeVisible();
    await expect(page.getByText(/Correct answer/i).first()).toBeVisible();
    await expect(page.getByText(/E2E explanation/i).first()).toBeVisible();

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );

    await verifyTeacherResult(page, assignmentId, expectedStudentName);
  });
});
