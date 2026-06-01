import { expect, test } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import { seedPracticeWorkflowData } from "../utils/seed";

test.describe("intervention tracking", () => {
  test("admin and teacher can create, view, note, and update student interventions", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const adminTitle = `E2E Parent Contact ${seed.runId}`;
    const teacherTitle = `E2E Teacher Follow-up ${seed.runId}`;
    const noteText = `E2E note ${seed.runId}: parent contact completed.`;

    await loginByApiAndStorage(
      page,
      request,
      credentials.admin.email,
      credentials.admin.password
    );
    await page.goto(`/admin/students/${seed.ids.student}/progress-report`);
    await expect(page.getByTestId("student-progress-report-page")).toBeVisible({
      timeout: 15_000
    });
    await page.getByTestId("intervention-create-button").click();
    await page.waitForURL(
      new RegExp(`/admin/students/${seed.ids.student}/interventions\\?create=1$`),
      { timeout: 15_000 }
    );

    await expect(page.getByTestId("student-interventions-page")).toBeVisible();
    await expect(page.getByTestId("intervention-form")).toBeVisible();
    await page.getByTestId("intervention-title-input").fill(adminTitle);
    await page
      .getByTestId("intervention-description-input")
      .fill("Called parent and scheduled a revision check-in.");
    await page.getByTestId("intervention-category-select").selectOption("parent_contact");
    await page.getByTestId("intervention-priority-select").selectOption("high");
    await page.getByTestId("intervention-submit-button").click();
    await expect(page.getByTestId("student-interventions-page")).toContainText(
      adminTitle,
      { timeout: 15_000 }
    );

    await page.goto("/admin/interventions");
    await expect(page.getByTestId("admin-intervention-dashboard")).toBeVisible({
      timeout: 15_000
    });
    await expect(page.getByTestId("intervention-list-page")).toContainText(
      adminTitle,
      { timeout: 15_000 }
    );

    await page.goto(`/admin/students/${seed.ids.student}/interventions`);
    await expect(page.getByTestId("student-interventions-page")).toContainText(
      adminTitle
    );
    await page
      .locator("tr", { hasText: adminTitle })
      .getByRole("link", { name: "View" })
      .click();
    await expect(page.getByTestId("intervention-detail-page")).toBeVisible({
      timeout: 15_000
    });
    await expect(page.getByTestId("intervention-detail-page")).toContainText(
      adminTitle
    );

    await page.getByTestId("intervention-note-input").fill(noteText);
    await page.getByTestId("intervention-add-note-button").click();
    await expect(page.getByTestId("intervention-note-card")).toContainText(
      noteText,
      { timeout: 15_000 }
    );

    await page.getByTestId("intervention-status-select").selectOption("resolved");
    await page.getByTestId("intervention-save-status-button").click();
    await expect(page.getByTestId("intervention-detail-page")).toContainText(
      "Resolved",
      { timeout: 15_000 }
    );

    await loginByApiAndStorage(
      page,
      request,
      seed.teacherCredentials.email,
      seed.teacherCredentials.password
    );
    await page.goto(`/teacher/students/${seed.ids.student}/progress-report`);
    await expect(page.getByTestId("student-progress-report-page")).toBeVisible({
      timeout: 15_000
    });
    await page.getByTestId("intervention-create-button").click();
    await page.waitForURL(
      new RegExp(`/teacher/students/${seed.ids.student}/interventions\\?create=1$`),
      { timeout: 15_000 }
    );

    await expect(page.getByTestId("student-interventions-page")).toContainText(
      adminTitle,
      { timeout: 15_000 }
    );
    await page.getByTestId("intervention-title-input").fill(teacherTitle);
    await page
      .getByTestId("intervention-description-input")
      .fill("Teacher scheduled a focused revision class.");
    await page
      .getByTestId("intervention-category-select")
      .selectOption("revision_class");
    await page.getByTestId("intervention-priority-select").selectOption("medium");
    await page.getByTestId("intervention-submit-button").click();
    await expect(page.getByTestId("student-interventions-page")).toContainText(
      teacherTitle,
      { timeout: 15_000 }
    );

    await page.goto("/teacher/interventions");
    await expect(page.getByTestId("intervention-list-page")).toContainText(
      teacherTitle,
      { timeout: 15_000 }
    );
  });
});
