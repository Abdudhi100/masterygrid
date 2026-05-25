import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

import { expect, test, type Locator, type Page } from "@playwright/test";

import { loginByApiAndStorage } from "../utils/auth";
import { credentials } from "../utils/env";
import {
  seedPracticeWorkflowData,
  type SeedPracticeWorkflowData
} from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";

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

const crcTable = new Uint32Array(256);
for (let index = 0; index < 256; index += 1) {
  let value = index;
  for (let bit = 0; bit < 8; bit += 1) {
    value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
  }
  crcTable[index] = value >>> 0;
}

function crc32(data: Buffer) {
  let crc = 0xffffffff;
  for (let index = 0; index < data.length; index += 1) {
    const byte = data[index];
    crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function csvCell(value: unknown) {
  const text = value === null || value === undefined ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function pngChunk(type: string, data: Buffer) {
  const typeBuffer = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  const crc = Buffer.alloc(4);

  length.writeUInt32BE(data.length, 0);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])), 0);

  return Buffer.concat([length, typeBuffer, data, crc]);
}

function createSyntheticPng() {
  const width = 32;
  const height = 32;
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const rows: Buffer[] = [];
  for (let y = 0; y < height; y += 1) {
    const row = Buffer.alloc(1 + width * 3);
    row[0] = 0;
    for (let x = 0; x < width; x += 1) {
      const offset = 1 + x * 3;
      const isLine =
        x === y ||
        x === width - y - 1 ||
        x === 0 ||
        y === 0 ||
        x === width - 1 ||
        y === height - 1;
      row[offset] = isLine ? 26 : 226;
      row[offset + 1] = isLine ? 32 : 245;
      row[offset + 2] = isLine ? 44 : 255;
    }
    rows.push(row);
  }

  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", zlib.deflateSync(Buffer.concat(rows))),
    pngChunk("IEND", Buffer.alloc(0))
  ]);
}

function createZip(entries: Array<{ name: string; data: Buffer }>) {
  const localParts: Buffer[] = [];
  const centralParts: Buffer[] = [];
  let offset = 0;

  for (const entry of entries) {
    const name = Buffer.from(entry.name, "utf8");
    const data = entry.data;
    const checksum = crc32(data);

    const localHeader = Buffer.alloc(30);
    localHeader.writeUInt32LE(0x04034b50, 0);
    localHeader.writeUInt16LE(20, 4);
    localHeader.writeUInt16LE(0x0800, 6);
    localHeader.writeUInt16LE(0, 8);
    localHeader.writeUInt16LE(0, 10);
    localHeader.writeUInt16LE(0, 12);
    localHeader.writeUInt32LE(checksum, 14);
    localHeader.writeUInt32LE(data.length, 18);
    localHeader.writeUInt32LE(data.length, 22);
    localHeader.writeUInt16LE(name.length, 26);
    localHeader.writeUInt16LE(0, 28);

    localParts.push(localHeader, name, data);

    const centralHeader = Buffer.alloc(46);
    centralHeader.writeUInt32LE(0x02014b50, 0);
    centralHeader.writeUInt16LE(20, 4);
    centralHeader.writeUInt16LE(20, 6);
    centralHeader.writeUInt16LE(0x0800, 8);
    centralHeader.writeUInt16LE(0, 10);
    centralHeader.writeUInt16LE(0, 12);
    centralHeader.writeUInt16LE(0, 14);
    centralHeader.writeUInt32LE(checksum, 16);
    centralHeader.writeUInt32LE(data.length, 20);
    centralHeader.writeUInt32LE(data.length, 24);
    centralHeader.writeUInt16LE(name.length, 28);
    centralHeader.writeUInt16LE(0, 30);
    centralHeader.writeUInt16LE(0, 32);
    centralHeader.writeUInt16LE(0, 34);
    centralHeader.writeUInt16LE(0, 36);
    centralHeader.writeUInt32LE(0, 38);
    centralHeader.writeUInt32LE(offset, 42);
    centralParts.push(centralHeader, name);

    offset += localHeader.length + name.length + data.length;
  }

  const centralDirectory = Buffer.concat(centralParts);
  const endRecord = Buffer.alloc(22);
  endRecord.writeUInt32LE(0x06054b50, 0);
  endRecord.writeUInt16LE(0, 4);
  endRecord.writeUInt16LE(0, 6);
  endRecord.writeUInt16LE(entries.length, 8);
  endRecord.writeUInt16LE(entries.length, 10);
  endRecord.writeUInt32LE(centralDirectory.length, 12);
  endRecord.writeUInt32LE(offset, 16);
  endRecord.writeUInt16LE(0, 20);

  return Buffer.concat([...localParts, centralDirectory, endRecord]);
}

function createTempZipImport(seed: SeedPracticeWorkflowData) {
  const uploadDir = path.join(process.cwd(), "e2e", "uploads");
  fs.mkdirSync(uploadDir, { recursive: true });

  const diagramFileName = `e2e_diagram_${seed.runId}.png`;
  const diagramDescription = `Synthetic E2E diagram ${seed.runId}`;
  const sourceName = `E2E ZIP Source ${seed.runId}`;
  const questionText = `E2E ZIP diagram ${seed.runId}: Which option matches the diagram?`;
  const explanation = `E2E ZIP diagram explanation for ${seed.runId}.`;

  const row = {
    subject: seed.names.subject,
    class_level: seed.names.classLevel,
    topic: seed.names.topic,
    source_name: sourceName,
    source_type: "jamb_past_question",
    exam_body: "E2E",
    year: 2025,
    difficulty: "medium",
    question_text: questionText,
    option_a: `E2E ZIP ${seed.runId} option A`,
    option_b: `E2E ZIP ${seed.runId} option B`,
    option_c: `E2E ZIP ${seed.runId} option C`,
    option_d: `E2E ZIP ${seed.runId} option D`,
    correct_option: "A",
    explanation,
    has_diagram: "true",
    diagram_file_name: diagramFileName,
    diagram_url: "",
    diagram_description: diagramDescription,
    needs_manual_review: "false"
  };

  const csv = [
    importColumns.join(","),
    importColumns.map((column) => csvCell(row[column as keyof typeof row])).join(",")
  ].join("\n");

  const zipPath = path.join(uploadDir, `question-import-diagram-${seed.runId}.zip`);
  const zip = createZip([
    { name: "questions.csv", data: Buffer.from(csv, "utf8") },
    {
      name: `diagrams/${diagramFileName}`,
      data: createSyntheticPng()
    }
  ]);
  fs.writeFileSync(zipPath, zip);

  return {
    zipPath,
    questionText,
    diagramDescription,
    explanation
  };
}

async function expectImageRendered(scope: Page | Locator) {
  const image = scope.getByTestId("question-media-image").first();
  await image.scrollIntoViewIfNeeded();
  await expect(image).toBeVisible({ timeout: 15_000 });
  await expect
    .poll(
      () =>
        image.evaluate((element) => {
          const img = element as HTMLImageElement;
          return img.complete && img.naturalWidth > 0 && img.naturalHeight > 0;
        }),
      { timeout: 15_000, message: "Waiting for question media image to render" }
    )
    .toBe(true);
}

async function validateZipImport(page: Page, zipPath: string, title: string) {
  await page.goto("/admin/question-bank/imports/new");
  await expect(
    page.getByRole("heading", { name: /^Import Questions$/i })
  ).toBeVisible();

  await page.getByTestId("import-title-input").fill(title);
  await page.getByTestId("import-file-input").setInputFiles(zipPath);
  await expect(page.getByText(path.basename(zipPath))).toBeVisible();

  await page.getByTestId("import-validate-button").click();

  const summary = page.getByTestId("import-preflight-summary");
  await expect(summary).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/^ZIP$/)).toBeVisible();
  await expect(summary).toContainText("Total Rows");
  await expect(summary).toContainText("1");
  await expect(summary).toContainText("Valid Rows");
  await expect(summary).toContainText("Invalid Rows");
  await expect(summary).toContainText("0");
  await expect(summary).toContainText("Can Import");
  await expect(summary).toContainText("Yes");
}

async function importValidatedZip(page: Page) {
  await expect(page.getByTestId("import-now-button")).toBeEnabled();
  await page.getByTestId("import-now-button").click();
  await page.waitForURL(/\/admin\/question-bank\/imports\/\d+$/, {
    timeout: 15_000
  });

  const detailSummary = page.getByTestId("import-detail-summary");
  await expect(detailSummary).toBeVisible({ timeout: 15_000 });
  await expect(detailSummary).toContainText("Total rows");
  await expect(detailSummary).toContainText("1");
  await expect(detailSummary).toContainText("Successful rows");
  await expect(detailSummary).toContainText("1");
  await expect(page.getByTestId("imported-question-link")).toHaveCount(1);
}

async function approveDiagramQuestion(
  page: Page,
  questionText: string,
  diagramDescription: string
) {
  await page.getByTestId("imported-question-link").first().click();
  await expect(
    page.getByRole("heading", { name: /^Question Detail$/i })
  ).toBeVisible();
  await expect(page.getByText(questionText)).toBeVisible();
  await expect(page.getByTestId("question-status-badge")).toContainText(/draft/i);
  await expect(page.getByTestId("question-diagram-badge")).toBeVisible();
  await expect(page.getByTestId("question-media-card")).toBeVisible();
  await expect(page.getByTestId("question-media-card").first()).toContainText(
    diagramDescription
  );
  await expectImageRendered(page);

  await page.getByTestId("question-approve-button").click();
  await expect(page.getByText("Question approved.")).toBeVisible({
    timeout: 15_000
  });
  await expect(page.getByTestId("question-status-badge")).toContainText(
    /approved/i
  );
}

async function startMediumPractice(page: Page, seed: SeedPracticeWorkflowData) {
  await page.goto("/student/practice");
  await expect(page.getByRole("heading", { name: /^Practice$/i })).toBeVisible();

  const subjectSelect = page.getByTestId("practice-subject-select");
  await expectSelectHasOption(
    subjectSelect,
    seed.names.subject,
    `subject select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await subjectSelect.selectOption({ label: seed.names.subject });

  const classLevelSelect = page.getByTestId("practice-class-level-select");
  await expectSelectHasOption(
    classLevelSelect,
    seed.names.classLevel,
    `class level select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await classLevelSelect.selectOption({ label: seed.names.classLevel });

  const topicSelect = page.getByTestId("practice-topic-select");
  await expectSelectHasOption(
    topicSelect,
    seed.names.topic,
    `topic select for seed IDs ${JSON.stringify(seed.ids)}`
  );
  await topicSelect.selectOption({ label: seed.names.topic });

  await page.getByTestId("practice-difficulty-select").selectOption("medium");
  await page.getByTestId("practice-question-count-input").fill("3");
  await page.getByTestId("practice-start-button").click();
  await page.waitForURL(/\/student\/practice\/\d+$/, { timeout: 15_000 });
}

async function answerAndSubmitPractice(page: Page, expectedCount: number) {
  const questionCards = page.getByTestId("practice-question-card");
  await expect(questionCards).toHaveCount(expectedCount, { timeout: 15_000 });

  await expect(page.getByText(/Correct answer/i)).toHaveCount(0);
  await expect(page.getByText(/Marks awarded/i)).toHaveCount(0);

  for (let index = 0; index < expectedCount; index += 1) {
    await questionCards.nth(index).getByTestId("practice-option-radio").first().check();
  }

  await expect(page.getByText(`Progress: ${expectedCount} / ${expectedCount}`)).toBeVisible();

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toMatch(/submit/i);
    await dialog.accept();
  });
  await page.getByTestId("practice-submit-button").click();
  await page.waitForURL(/\/student\/practice\/\d+\/result$/, {
    timeout: 15_000
  });
}

test.describe("ZIP diagram question import flow", () => {
  test("admin imports and approves a ZIP diagram question that appears in student practice", async ({
    page,
    request
  }) => {
    test.setTimeout(180_000);

    const seed = await seedPracticeWorkflowData(request);
    const importTitle = `E2E ZIP Import ${seed.runId}`;
    const { zipPath, questionText, diagramDescription, explanation } =
      createTempZipImport(seed);

    try {
      await loginByApiAndStorage(
        page,
        request,
        credentials.admin.email,
        credentials.admin.password
      );

      await validateZipImport(page, zipPath, importTitle);
      await importValidatedZip(page);
      await approveDiagramQuestion(page, questionText, diagramDescription);

      await loginByApiAndStorage(
        page,
        request,
        seed.studentCredentials.email,
        seed.studentCredentials.password
      );

      await startMediumPractice(page, seed);
      await expect(
        page.getByRole("heading", { name: `${seed.names.subject} Practice` })
      ).toBeVisible();

      const diagramQuestionCard = page
        .getByTestId("practice-question-card")
        .filter({ hasText: questionText });
      await expect(diagramQuestionCard).toBeVisible({ timeout: 15_000 });
      await expect(diagramQuestionCard.getByText(explanation)).toHaveCount(0);
      await expect(
        diagramQuestionCard.getByTestId("practice-question-media")
      ).toContainText(diagramDescription);
      await expect(
        diagramQuestionCard
          .getByTestId("practice-question-media")
          .getByTestId("question-media-card")
      ).toBeVisible();
      await expectImageRendered(
        diagramQuestionCard.getByTestId("practice-question-media")
      );

      await answerAndSubmitPractice(page, 3);

      await expect(page.getByTestId("practice-result-summary")).toBeVisible();
      const diagramCorrectionCard = page
        .getByTestId("practice-correction-card")
        .filter({ hasText: questionText });
      await expect(diagramCorrectionCard).toBeVisible({ timeout: 15_000 });
      await expect(diagramCorrectionCard).toContainText("Correct answer");
      await expect(diagramCorrectionCard).toContainText(explanation);
      await expect(
        diagramCorrectionCard.getByTestId("practice-result-media")
      ).toContainText(diagramDescription);
      await expect(
        diagramCorrectionCard
          .getByTestId("practice-result-media")
          .getByTestId("question-media-card")
      ).toBeVisible();
      await expectImageRendered(
        diagramCorrectionCard.getByTestId("practice-result-media")
      );
    } finally {
      fs.rmSync(zipPath, { force: true });
    }
  });
});
