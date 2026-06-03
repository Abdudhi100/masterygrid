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

function localDateTimeValue(date: Date) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

async function createAssignmentFromTeacherUI(
  page: Page,
  seed: SeedPracticeWorkflowData,
  assignmentTitle: string,
  dueAt: Date
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
  await page.getByTestId("assignment-due-at-input").fill(localDateTimeValue(dueAt));
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
  await expect(page.getByTestId("assignment-deadline-status-badge")).toContainText(
    /overdue/i
  );
  return assignmentId;
}

async function expectStudentCannotStartOverdueAssignment(
  page: Page,
  assignmentId: number,
  assignmentTitle: string
) {
  await page.goto(`/student/assignments/${assignmentId}`);
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();
  await expect(page.getByTestId("student-assignment-deadline-badge")).toContainText(
    /overdue/i
  );
  await expect(page.getByTestId("assignment-start-button")).toBeDisabled();
}

async function extendDeadlineFromTeacherUI(page: Page, assignmentId: number) {
  await page.goto(`/teacher/assignments/${assignmentId}`);
  const deadlineForm = page.getByTestId("assignment-extend-deadline-form");
  await expect(deadlineForm).toBeVisible();

  const futureDue = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000);
  const lateUntil = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  await deadlineForm
    .getByTestId("assignment-due-at-input")
    .fill(localDateTimeValue(futureDue));
  await page.getByTestId("assignment-allow-late-checkbox").check();
  await deadlineForm
    .getByTestId("assignment-late-deadline-input")
    .fill(localDateTimeValue(lateUntil));
  await expect(deadlineForm.getByTestId("assignment-due-at-input")).toHaveValue(
    localDateTimeValue(futureDue)
  );
  await expect(page.getByTestId("assignment-allow-late-checkbox")).toBeChecked();
  const extendResponsePromise = page.waitForResponse((response) =>
    response.url().includes(`/api/assignments/${assignmentId}/extend-deadline/`)
  );
  await page.getByTestId("assignment-extend-deadline-button").click();
  const extendResponse = await extendResponsePromise;
  if (!extendResponse.ok()) {
    throw new Error(
      `Extend deadline failed with ${extendResponse.status()}: ${await extendResponse.text()}`
    );
  }

  await expect(page.getByText("Assignment deadline extended.")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("assignment-deadline-status-badge")).toContainText(
    /open|due soon/i
  );
}

async function openExtendedAssignmentNotification(
  page: Page,
  assignmentId: number,
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
  }).filter({
    hasText: "Assignment deadline extended"
  });
  await expect(item).toBeVisible();
  await item.getByRole("button", { name: "Open" }).click();
  await page.waitForURL(new RegExp(`/student/assignments/${assignmentId}$`), {
    timeout: 15_000
  });
}

async function submitAssignment(page: Page, assignmentTitle: string) {
  await expect(page.getByRole("heading", { name: assignmentTitle })).toBeVisible();
  await expect(page.getByTestId("student-assignment-deadline-badge")).toContainText(
    /open|due soon/i
  );
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
  await expect(page.getByTestId("submission-late-badge")).toContainText(/late/i);
}

test.describe("assignment deadline flow", () => {
  test("teacher extends an overdue assignment and late submission is tracked", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const assignmentTitle = `E2E Deadline Assignment ${seed.runId}`;
    const overdueAt = new Date(Date.now() - 60 * 60 * 1000);

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    const assignmentId = await createAssignmentFromTeacherUI(
      page,
      seed,
      assignmentTitle,
      overdueAt
    );

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );
    await expectStudentCannotStartOverdueAssignment(
      page,
      assignmentId,
      assignmentTitle
    );

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await extendDeadlineFromTeacherUI(page, assignmentId);

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );
    await openExtendedAssignmentNotification(page, assignmentId, assignmentTitle);
    await submitAssignment(page, assignmentTitle);

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await page.goto(`/teacher/assignments/${assignmentId}/results`);
    await expect(
      page.getByRole("heading", { name: /^Assignment Results$/i })
    ).toBeVisible();
    await expect(page.getByTestId("submission-late-badge")).toContainText(/late/i);
  });
});
