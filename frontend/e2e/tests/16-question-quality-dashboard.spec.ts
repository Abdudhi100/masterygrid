import {
  expect,
  test,
  type APIRequestContext,
  type Locator,
  type Page
} from "@playwright/test";

import { apiPost } from "../utils/api";
import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import {
  seedPracticeWorkflowData,
  type SeedPracticeWorkflowData
} from "../utils/seed";

type CreatedQuestion = {
  id: number;
  status: string;
  question_text: string;
};

type QualityQuestionOverrides = {
  questionText: string;
  explanation?: string;
  difficulty?: "easy" | "medium" | "hard";
  hasDiagram?: boolean;
  needsManualReview?: boolean;
  diagramDescription?: string;
  optionSuffix?: string;
};

function qualityQuestionPayload(
  seed: SeedPracticeWorkflowData,
  {
    questionText,
    explanation = `E2E quality explanation for ${seed.runId}.`,
    difficulty = "medium",
    hasDiagram = false,
    needsManualReview = false,
    diagramDescription = "",
    optionSuffix = questionText
  }: QualityQuestionOverrides
) {
  return {
    school: seed.ids.school,
    subject: seed.ids.subject,
    class_level: seed.ids.classLevel,
    topic: seed.ids.topic,
    source: seed.ids.questionSource,
    question_text: questionText,
    explanation,
    difficulty,
    status: "draft",
    is_active: true,
    has_diagram: hasDiagram,
    diagram_description: diagramDescription,
    needs_manual_review: needsManualReview,
    options: ["A", "B", "C", "D"].map((label) => ({
      label,
      text: `E2E quality ${label} option for ${optionSuffix}`,
      is_correct: label === "A"
    }))
  };
}

async function createQualityQuestion(
  request: APIRequestContext,
  seed: SeedPracticeWorkflowData,
  overrides: QualityQuestionOverrides
) {
  return apiPost<CreatedQuestion>(
    request,
    "question-bank/questions/",
    seed.adminToken,
    qualityQuestionPayload(seed, overrides)
  );
}

async function openQualityDashboard(page: Page) {
  await page.goto("/admin/question-bank/quality");
  await expect(
    page.getByRole("heading", { name: /^Question Quality$/i })
  ).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("question-quality-dashboard")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("question-quality-summary")).toBeVisible();
}

async function selectQualityTab(page: Page, label: string) {
  await page.getByTestId("question-quality-tab").filter({ hasText: label }).click();
}

function qualityRow(page: Page, text: string) {
  return page.getByTestId("question-quality-row").filter({ hasText: text });
}

async function expectQualityRow(
  page: Page,
  tabLabel: string,
  questionText: string,
  expectedIssue: RegExp
) {
  await selectQualityTab(page, tabLabel);
  const row = qualityRow(page, questionText).first();
  await expect(row).toBeVisible({ timeout: 15_000 });
  await expect(row.getByTestId("question-quality-issue-badge")).toContainText(
    expectedIssue
  );
  return row;
}

async function openQuestionFromRow(page: Page, row: Locator, questionId: number) {
  await row.getByTestId("question-quality-view-link").click();
  await expect.poll(
    async () => new URL(page.url()).pathname,
    { timeout: 15_000, message: `Waiting to open question ${questionId}` }
  ).toMatch(new RegExp(`/admin/question-bank/${questionId}$`));
}

test.describe("question quality dashboard flow", () => {
  test("admin reviews quality queues and bulk approves a ready question", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const missingExplanationText = `E2E quality ${seed.runId}: missing explanation question`;
    const diagramIssueText = `E2E quality ${seed.runId}: diagram review question`;
    const duplicateText = `E2E quality ${seed.runId}: duplicate suspect question`;
    const readyText = `E2E quality ${seed.runId}: ready for approval question`;

    const missingExplanation = await createQualityQuestion(request, seed, {
      questionText: missingExplanationText,
      explanation: ""
    });
    const diagramIssue = await createQualityQuestion(request, seed, {
      questionText: diagramIssueText,
      hasDiagram: true,
      needsManualReview: true,
      diagramDescription: `E2E quality diagram needs review ${seed.runId}`
    });
    await createQualityQuestion(request, seed, {
      questionText: duplicateText,
      optionSuffix: `${duplicateText} first`
    });
    await createQualityQuestion(request, seed, {
      questionText: duplicateText,
      optionSuffix: `${duplicateText} second`
    });
    const readyQuestion = await createQualityQuestion(request, seed, {
      questionText: readyText,
      difficulty: "easy"
    });

    await loginByApiAndStorage(
      page,
      request,
      credentials.admin.email,
      credentials.admin.password
    );

    await openQualityDashboard(page);

    await expectQualityRow(
      page,
      "Needs Review",
      diagramIssueText,
      /needs manual review/i
    );
    await expectQualityRow(
      page,
      "Missing Explanations",
      missingExplanationText,
      /missing explanation/i
    );
    await expectQualityRow(
      page,
      "Diagram Issues",
      diagramIssueText,
      /diagram issue/i
    );
    await expectQualityRow(
      page,
      "Duplicates",
      duplicateText,
      /duplicate suspect/i
    );

    const missingRow = await expectQualityRow(
      page,
      "Missing Explanations",
      missingExplanationText,
      /missing explanation/i
    );
    await openQuestionFromRow(page, missingRow, missingExplanation.id);
    await expect(page.locator("body")).toContainText(missingExplanationText);
    await expect(page.getByTestId("question-status-badge")).toContainText(/draft/i);

    await openQualityDashboard(page);
    const readyRow = await expectQualityRow(
      page,
      "Ready for Approval",
      readyText,
      /ready for approval/i
    );
    await expect(readyRow).not.toContainText(diagramIssueText);
    await readyRow.getByLabel(`Select question ${readyQuestion.id}`).check();
    await page.getByTestId("question-quality-bulk-action").click();
    await expect(page.getByText("1 question(s) approved.")).toBeVisible({
      timeout: 15_000
    });

    await page.goto(`/admin/question-bank/${readyQuestion.id}`);
    await expect(page.locator("body")).toContainText(readyText, {
      timeout: 15_000
    });
    await expect(page.getByTestId("question-status-badge")).toContainText(
      /approved/i
    );

    await page.goto(`/admin/question-bank/${diagramIssue.id}`);
    await expect(page.locator("body")).toContainText(diagramIssueText, {
      timeout: 15_000
    });
    await expect(page.getByTestId("question-status-badge")).toContainText(/draft/i);
  });
});
