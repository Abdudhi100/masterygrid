import { expect, test, type Page } from "@playwright/test";

import { apiPost } from "../utils/api";
import { loginByApiAndStorage } from "../utils/auth";
import { seedPracticeWorkflowData } from "../utils/seed";

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

async function submitLowScoreAssignment(page: Page, assignmentTitle: string) {
  await openStudentAssignment(page, assignmentTitle);
  await page.getByTestId("assignment-start-button").click();
  await page.waitForURL(/\/student\/assignments\/\d+\/attempt\?submissionId=\d+$/, {
    timeout: 15_000
  });

  const questionCards = page.getByTestId("assignment-question-card");
  await expect(questionCards).toHaveCount(5, { timeout: 15_000 });
  await expect(page.getByText(/Correct answer/i)).toHaveCount(0);

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

test.describe("teacher dashboard flow", () => {
  test("teacher sees action-center summaries and follows a quick action", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const assignmentTitle = `E2E Practice Assignment ${seed.runId}`;
    const interventionTitle = `E2E Dashboard Follow-up ${seed.runId}`;

    await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );
    await submitLowScoreAssignment(page, assignmentTitle);

    await apiPost(
      request,
      "interventions/",
      seed.adminToken,
      {
        student: seed.ids.student,
        assigned_to: seed.ids.teacher,
        title: interventionTitle,
        description: "E2E teacher dashboard intervention follow-up.",
        category: "academic_support",
        priority: "high",
        source_subject: seed.ids.subject,
        source_topic: seed.ids.topic,
        source_class_arm: seed.ids.classArm
      }
    );

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await page.goto("/teacher/dashboard");
    await expect(
      page.getByRole("heading", { name: /teacher dashboard/i })
    ).toBeVisible();
    await expect(page.getByTestId("teacher-dashboard-page")).toBeVisible();
    await expect(page.getByTestId("teacher-dashboard-summary")).toContainText(
      "Active assignments"
    );
    await expect(page.getByTestId("teacher-dashboard-assignment-alerts")).toBeVisible();
    await expect(page.getByTestId("teacher-dashboard-weak-students")).toContainText(
      `E2E Student ${seed.runId}`,
      { timeout: 15_000 }
    );
    await expect(page.getByTestId("teacher-dashboard-weak-topics")).toContainText(
      seed.names.topic
    );
    await expect(page.getByTestId("teacher-dashboard-remediation")).toContainText(
      seed.names.topic
    );
    await expect(page.getByTestId("teacher-dashboard-interventions")).toContainText(
      interventionTitle
    );
    await expect(page.getByTestId("teacher-dashboard-notifications")).toContainText(
      "Assignment submitted"
    );

    const createAssignmentAction = page
      .getByTestId("teacher-dashboard-quick-action")
      .filter({ hasText: "Create assignment" });
    await expect(createAssignmentAction).toBeVisible();
    await createAssignmentAction.click();
    await page.waitForURL(/\/teacher\/assignments\/new$/, { timeout: 15_000 });
    await expect(
      page.getByRole("heading", { name: /^Create Assignment$/i })
    ).toBeVisible();
  });
});
