import fs from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials, testPassword } from "../utils/env";
import { seedPracticeWorkflowData, type SeedPracticeWorkflowData } from "../utils/seed";

function csvCell(value: unknown) {
  const text = value === null || value === undefined ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function writeCsv(runId: string, fileName: string, columns: string[], rows: Record<string, unknown>[]) {
  const uploadDir = path.join(process.cwd(), "e2e", "uploads");
  fs.mkdirSync(uploadDir, { recursive: true });
  const csv = [
    columns.join(","),
    ...rows.map((row) => columns.map((column) => csvCell(row[column])).join(","))
  ].join("\n");
  const filePath = path.join(uploadDir, `${fileName}-${runId}.csv`);
  fs.writeFileSync(filePath, csv, "utf8");
  return filePath;
}

function createStudentCsv(seed: SeedPracticeWorkflowData) {
  const columns = [
    "full_name",
    "email",
    "admission_number",
    "class_arm",
    "guardian_name",
    "guardian_phone",
    "password"
  ];
  const students = [1, 2].map((index) => ({
    full_name: `E2E Bulk Student ${index} ${seed.runId}`,
    email: `e2e.bulk.student.${index}.${seed.runId}@masterygrid.test`,
    admission_number: `E2E-BULK-${seed.runId}-${index}`,
    class_arm: seed.names.classArm,
    guardian_name: `E2E Guardian ${index}`,
    guardian_phone: `08000000${index}`,
    password: testPassword
  }));
  return {
    filePath: writeCsv(seed.runId, "bulk-students", columns, students),
    students
  };
}

function createTeacherCsv(seed: SeedPracticeWorkflowData) {
  const columns = ["full_name", "email", "staff_id", "phone_number", "password"];
  const teachers = [
    {
      full_name: `E2E Bulk Teacher ${seed.runId}`,
      email: `e2e.bulk.teacher.${seed.runId}@masterygrid.test`,
      staff_id: `E2E-BULK-T-${seed.runId}`,
      phone_number: "08090000001",
      password: testPassword
    }
  ];
  return {
    filePath: writeCsv(seed.runId, "bulk-teachers", columns, teachers),
    teachers
  };
}

async function validateAndImport(
  page: Page,
  importType: "students" | "teachers",
  filePath: string,
  expectedValidRows: number
) {
  await page.goto(`/admin/imports/new?type=${importType}`);
  await expect(page.getByRole("heading", { name: /^New Bulk Import$/i })).toBeVisible();
  await expect(page.getByTestId("bulk-import-type-select")).toHaveValue(importType);

  await page.getByTestId("bulk-import-file-input").setInputFiles(filePath);
  await expect(page.getByText(path.basename(filePath))).toBeVisible();

  await page.getByTestId("bulk-import-validate-button").click();
  const summary = page.getByTestId("bulk-import-preflight-summary");
  await expect(summary).toBeVisible({ timeout: 15_000 });
  await expect(summary).toContainText("Total Rows");
  await expect(summary).toContainText(String(expectedValidRows));
  await expect(summary).toContainText("Valid Rows");
  await expect(summary).toContainText("Invalid Rows");
  await expect(summary).toContainText("0");
  await expect(summary).toContainText("Can Import");
  await expect(summary).toContainText("Yes");

  await expect(page.getByTestId("bulk-import-now-button")).toBeEnabled();
  await page.getByTestId("bulk-import-now-button").click();
  await page.waitForURL(/\/admin\/imports\/\d+\?domain=accounts$/, {
    timeout: 15_000
  });
  await expect(page.getByTestId("bulk-import-detail-page")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("bulk-import-detail-page")).toContainText(
    "Imported rows"
  );
  await expect(page.getByTestId("bulk-import-detail-page")).toContainText(
    String(expectedValidRows)
  );
  await expect(page.getByTestId("bulk-import-row-status")).toHaveCount(
    expectedValidRows
  );
}

async function expectAdminListContains(page: Page, pathName: string, texts: string[]) {
  await page.goto(pathName);
  for (const text of texts) {
    await expect(page.getByText(text)).toBeVisible({ timeout: 15_000 });
  }
}

test.describe("bulk user import flow", () => {
  test("school admin validates and imports student and teacher CSV files", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const studentCsv = createStudentCsv(seed);
    const teacherCsv = createTeacherCsv(seed);

    try {
      await loginByApiAndStorage(
        page,
        request,
        credentials.admin.email,
        credentials.admin.password
      );

      await validateAndImport(page, "students", studentCsv.filePath, 2);
      await expectAdminListContains(
        page,
        "/admin/students",
        studentCsv.students.map((student) => student.email)
      );

      await validateAndImport(page, "teachers", teacherCsv.filePath, 1);
      await expectAdminListContains(
        page,
        "/admin/teachers",
        teacherCsv.teachers.map((teacher) => teacher.email)
      );

      await loginByApiAndStorage(
        page,
        request,
        studentCsv.students[0].email,
        testPassword
      );
      await expect(
        page.getByRole("heading", { name: /student dashboard/i })
      ).toBeVisible();
    } finally {
      fs.rmSync(studentCsv.filePath, { force: true });
      fs.rmSync(teacherCsv.filePath, { force: true });
    }
  });
});
