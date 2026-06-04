import { expect, test, type APIRequestContext } from "@playwright/test";

import { apiPost, loginApi } from "../utils/api";
import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";

type StartedSubmission = {
  id: number;
  questions: Array<{
    assignment_question: number;
    options: Array<{ id: number }>;
  }>;
};

async function submitLowScoreAssignmentByApi(
  request: APIRequestContext,
  seed: SeedPracticeWorkflowData
) {
  const tokenPair = await loginApi(
    request,
    seed.studentCredentials.email,
    seed.studentCredentials.password
  );
  const submission = await apiPost<StartedSubmission>(
    request,
    "submissions/start-assignment/",
    tokenPair.access,
    {
      assignment: seed.ids.assignment
    }
  );
  await apiPost(
    request,
    `submissions/${submission.id}/submit/`,
    tokenPair.access,
    {
      answers: submission.questions.map((question) => ({
        assignment_question: question.assignment_question,
        selected_option: question.options[0].id
      }))
    }
  );
}

test.describe("school admin dashboard", () => {
  test("admin sees command-center sections and follows a quick action", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const interventionTitle = `E2E Admin Dashboard Follow-up ${seed.runId}`;

    await submitLowScoreAssignmentByApi(request, seed);

    await apiPost(
      request,
      "interventions/",
      seed.adminToken,
      {
        student: seed.ids.student,
        assigned_to: seed.ids.teacher,
        title: interventionTitle,
        description: "E2E school admin dashboard intervention follow-up.",
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
      credentials.admin.email,
      credentials.admin.password
    );
    await page.goto("/admin/dashboard");
    await expect(
      page.getByRole("heading", { name: /school dashboard/i })
    ).toBeVisible();
    await expect(page.getByTestId("admin-dashboard-page")).toBeVisible();
    await expect(page.getByTestId("admin-dashboard-summary")).toContainText(
      "Students"
    );
    await expect(page.getByTestId("admin-dashboard-setup")).toContainText(
      /complete|progress|onboarding/i
    );
    await expect(page.getByTestId("admin-dashboard-risk-overview")).toContainText(
      /High-Risk Classes|Class risk signals/i,
      { timeout: 15_000 }
    );
    await expect(page.getByTestId("admin-dashboard-compliance")).toContainText(
      "E2E Practice Assignment"
    );
    await expect(page.getByTestId("admin-dashboard-interventions")).toContainText(
      interventionTitle
    );
    await expect(page.getByTestId("admin-dashboard-teachers")).toBeVisible();
    await expect(page.getByTestId("admin-dashboard-notifications")).toBeVisible();
    await expect(page.getByTestId("admin-dashboard-audit")).toBeVisible();

    const setupAction = page
      .getByTestId("admin-dashboard-quick-action")
      .filter({ hasText: /setup/i })
      .first();
    await expect(setupAction).toBeVisible();
    await setupAction.click();
    await page.waitForURL(/\/admin\/setup$/, { timeout: 15_000 });
    await expect(page.getByTestId("school-setup-page")).toBeVisible();
  });
});
