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
  await page.getByTestId("assignment-publish-button").click();
  await page.waitForURL(/\/teacher\/assignments\/\d+$/, { timeout: 15_000 });

  const assignmentId = assignmentIdFromUrl(page.url());
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();
  await expect(page.getByTestId("assignment-status-badge")).toContainText(
    /published/i
  );
  return assignmentId;
}

async function openStudentAssignmentFromNotification(
  page: Page,
  assignmentTitle: string
) {
  await expect(page.getByTestId("notification-bell")).toBeVisible();
  await expect(page.getByTestId("notification-unread-count")).toBeVisible({
    timeout: 15_000
  });
  await page.getByTestId("notification-bell").click();
  await expect(page.getByTestId("notification-dropdown")).toBeVisible();

  const item = page.getByTestId("notification-item").filter({
    hasText: assignmentTitle
  });
  await expect(item).toContainText("New assignment published");
  await item.getByRole("button", { name: "Open" }).click();
  await page.waitForURL(/\/student\/assignments\/\d+$/, { timeout: 15_000 });
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();
}

async function submitCurrentAssignment(page: Page, assignmentTitle: string) {
  await page.getByTestId("assignment-start-button").click();
  await page.waitForURL(/\/student\/assignments\/\d+\/attempt\?submissionId=\d+$/, {
    timeout: 15_000
  });
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();

  const questionCards = page.getByTestId("assignment-question-card");
  await expect(questionCards).toHaveCount(5, { timeout: 15_000 });
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

async function openTeacherSubmissionNotification(
  page: Page,
  assignmentTitle: string,
  assignmentId: number
) {
  await expect(page.getByTestId("notification-bell")).toBeVisible();
  await expect(page.getByTestId("notification-unread-count")).toBeVisible({
    timeout: 15_000
  });
  await page.getByTestId("notification-bell").click();
  await expect(page.getByTestId("notification-dropdown")).toBeVisible();

  const item = page.getByTestId("notification-item").filter({
    hasText: assignmentTitle
  });
  await expect(item).toContainText("Assignment submitted");
  await item.getByRole("button", { name: "Open" }).click();
  await page.waitForURL(
    new RegExp(`/teacher/assignments/${assignmentId}/results$`),
    { timeout: 15_000 }
  );
  await expect(
    page.getByRole("heading", { name: /^Assignment Results$/i })
  ).toBeVisible();
  await expect(page.getByTestId("notification-unread-count")).toHaveCount(0);
}

test.describe("notifications flow", () => {
  test("assignment publish and submission create actionable notifications", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const assignmentTitle = `E2E Notification Assignment ${seed.runId}`;

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
    await openStudentAssignmentFromNotification(page, assignmentTitle);
    await submitCurrentAssignment(page, assignmentTitle);

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await openTeacherSubmissionNotification(page, assignmentTitle, assignmentId);
  });
});
