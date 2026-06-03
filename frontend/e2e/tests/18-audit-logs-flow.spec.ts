import { expect, test, type APIRequestContext } from "@playwright/test";

import { apiPost } from "../utils/api";
import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import {
  seedPracticeWorkflowData,
  type SeedPracticeWorkflowData
} from "../utils/seed";

type CreatedQuestion = {
  id: number;
  question_text: string;
};

function auditQuestionPayload(seed: SeedPracticeWorkflowData, questionText: string) {
  return {
    school: seed.ids.school,
    subject: seed.ids.subject,
    class_level: seed.ids.classLevel,
    topic: seed.ids.topic,
    source: seed.ids.questionSource,
    question_text: questionText,
    explanation: `E2E audit explanation for ${seed.runId}.`,
    difficulty: "medium",
    status: "draft",
    is_active: true,
    options: ["A", "B", "C", "D"].map((label) => ({
      label,
      text: `E2E audit option ${label} for ${seed.runId}`,
      is_correct: label === "A"
    }))
  };
}

async function createAndApproveAuditQuestion(
  request: APIRequestContext,
  seed: SeedPracticeWorkflowData,
  questionText: string
) {
  const question = await apiPost<CreatedQuestion>(
    request,
    "question-bank/questions/",
    seed.adminToken,
    auditQuestionPayload(seed, questionText)
  );
  await apiPost<CreatedQuestion>(
    request,
    `question-bank/questions/${question.id}/approve/`,
    seed.adminToken,
    {}
  );
  return question;
}

test.describe("audit logs flow", () => {
  test("school admin finds an audit log for an approved question", async ({
    page,
    request
  }) => {
    test.setTimeout(150_000);

    const seed = await seedPracticeWorkflowData(request);
    const questionText = `E2E audit ${seed.runId}: approved question activity`;
    await createAndApproveAuditQuestion(request, seed, questionText);

    await loginByApiAndStorage(
      page,
      request,
      credentials.admin.email,
      credentials.admin.password
    );

    await page.goto("/admin/audit-logs");
    await expect(page.getByTestId("audit-logs-page")).toBeVisible({
      timeout: 15_000
    });
    await expect(page.getByRole("heading", { name: /^Audit Logs$/i })).toBeVisible();

    await page.getByTestId("audit-log-filter-category").selectOption("question_bank");
    await page.getByTestId("audit-log-search-input").fill(questionText);
    await page.getByRole("button", { name: /^Apply Filters$/i }).click();

    const row = page.getByTestId("audit-log-row").filter({ hasText: questionText });
    await expect(row).toBeVisible({ timeout: 15_000 });
    await expect(row).toContainText(/question approved/i);
    await expect(row).toContainText(/question bank/i);

    await row.getByTestId("audit-log-metadata-toggle").click();
    await expect(page.locator("pre").filter({ hasText: "approved" })).toBeVisible();
  });
});
