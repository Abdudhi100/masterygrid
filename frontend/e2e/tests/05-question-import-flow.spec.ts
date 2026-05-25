import fs from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";

const importColumns = [
  "subject",
  "class_level",
  "topic",
  "source_name",
  "source_type",
  "exam_body",
  "year",
  "difficulty",
  "question_text",
  "option_a",
  "option_b",
  "option_c",
  "option_d",
  "correct_option",
  "explanation",
  "has_diagram",
  "diagram_file_name",
  "diagram_url",
  "diagram_description",
  "needs_manual_review"
];

function csvCell(value: unknown) {
  const text = value === null || value === undefined ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function createTempQuestionImportCsv(seed: SeedPracticeWorkflowData) {
  const uploadDir = path.join(process.cwd(), "e2e", "uploads");
  fs.mkdirSync(uploadDir, { recursive: true });

  const sourceName = `E2E Import Source ${seed.runId}`;
  const questionTexts = [
    `E2E imported ${seed.runId} question 1: Which option is marked correct?`,
    `E2E imported ${seed.runId} question 2: Which option should be selected?`
  ];

  const rows = questionTexts.map((questionText, index) => ({
    subject: seed.names.subject,
    class_level: seed.names.classLevel,
    topic: seed.names.topic,
    source_name: sourceName,
    source_type: "jamb_past_question",
    exam_body: "E2E",
    year: 2026,
    difficulty: index === 0 ? "easy" : "medium",
    question_text: questionText,
    option_a: `E2E import ${seed.runId} question ${index + 1} option A`,
    option_b: `E2E import ${seed.runId} question ${index + 1} option B`,
    option_c: `E2E import ${seed.runId} question ${index + 1} option C`,
    option_d: `E2E import ${seed.runId} question ${index + 1} option D`,
    correct_option: index === 0 ? "A" : "B",
    explanation: `E2E synthetic explanation ${index + 1} for ${seed.runId}.`,
    has_diagram: "false",
    diagram_file_name: "",
    diagram_url: "",
    diagram_description: "",
    needs_manual_review: "false"
  }));

  const csv = [
    importColumns.join(","),
    ...rows.map((row) =>
      importColumns.map((column) => csvCell(row[column as keyof typeof row])).join(",")
    )
  ].join("\n");

  const filePath = path.join(uploadDir, `question-import-${seed.runId}.csv`);
  fs.writeFileSync(filePath, csv, "utf8");

  return { filePath, questionTexts, sourceName };
}

async function validateQuestionImport(page: Page, filePath: string, title: string) {
  await page.goto("/admin/question-bank/imports/new");
  await expect(
    page.getByRole("heading", { name: /^Import Questions$/i })
  ).toBeVisible();

  await page.getByTestId("import-title-input").fill(title);
  await page.getByTestId("import-file-input").setInputFiles(filePath);
  await expect(page.getByText(path.basename(filePath))).toBeVisible();

  await page.getByTestId("import-validate-button").click();

  const summary = page.getByTestId("import-preflight-summary");
  await expect(summary).toBeVisible({ timeout: 15_000 });
  await expect(summary).toContainText("Total Rows");
  await expect(summary).toContainText("2");
  await expect(summary).toContainText("Valid Rows");
  await expect(summary).toContainText("Invalid Rows");
  await expect(summary).toContainText("0");
  await expect(summary).toContainText("Can Import");
  await expect(summary).toContainText("Yes");
}

async function importValidatedQuestionFile(page: Page) {
  await expect(page.getByTestId("import-now-button")).toBeEnabled();
  await page.getByTestId("import-now-button").click();
  await page.waitForURL(/\/admin\/question-bank\/imports\/\d+$/, {
    timeout: 15_000
  });

  const detailSummary = page.getByTestId("import-detail-summary");
  await expect(detailSummary).toBeVisible({ timeout: 15_000 });
  await expect(detailSummary).toContainText("Total rows");
  await expect(detailSummary).toContainText("2");
  await expect(detailSummary).toContainText("Successful rows");
  await expect(detailSummary).toContainText("2");
  await expect(page.getByTestId("imported-question-link")).toHaveCount(2);
}

async function approveImportedQuestion(page: Page, expectedQuestionText: string) {
  await page.getByTestId("imported-question-link").first().click();
  await expect(
    page.getByRole("heading", { name: /^Question Detail$/i })
  ).toBeVisible();
  await expect(page.getByText(expectedQuestionText)).toBeVisible();
  await expect(page.getByTestId("question-status-badge")).toContainText(/draft/i);

  await page.getByTestId("question-approve-button").click();
  await expect(page.getByText("Question approved.")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("question-status-badge")).toContainText(
    /approved/i
  );
}

async function verifyApprovedQuestionInList(
  page: Page,
  expectedQuestionText: string
) {
  await page.goto("/admin/question-bank?status=approved");
  await expect(page.getByRole("heading", { name: /^Question Bank$/i })).toBeVisible();

  await page.getByLabel("Search").fill(expectedQuestionText);
  const row = page.locator("tbody tr").filter({ hasText: expectedQuestionText });
  await expect(row).toBeVisible({ timeout: 15_000 });
  await expect(row).toContainText(/approved/i);
}

test.describe("question import and approval flow", () => {
  test("admin validates/imports CSV, approves imported draft, and finds approved question", async ({
    page,
    request
  }) => {
    test.setTimeout(150_000);

    const seed = await seedPracticeWorkflowData(request);
    const importTitle = `E2E Import ${seed.runId}`;
    const { filePath, questionTexts } = createTempQuestionImportCsv(seed);

    try {
      await loginByApiAndStorage(
        page,
        request,
        credentials.admin.email,
        credentials.admin.password
      );

      await validateQuestionImport(page, filePath, importTitle);
      await importValidatedQuestionFile(page);
      await approveImportedQuestion(page, questionTexts[0]);
      await verifyApprovedQuestionInList(page, questionTexts[0]);
    } finally {
      fs.rmSync(filePath, { force: true });
    }
  });
});
