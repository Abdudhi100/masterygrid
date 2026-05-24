import { expect, test, type APIRequestContext } from "@playwright/test";

import {
  loginByApiAndStorage
} from "../utils/auth";
import { apiGet } from "../utils/api";
import { seedPracticeWorkflowData } from "../utils/seed";
import { expectSelectHasOption } from "../utils/select";
import type { SeedPracticeWorkflowData } from "../utils/seed";

type ApiListResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

type ApiNamedRecord = {
  id: number;
  name?: string;
  title?: string;
};

function unwrapList<T>(payload: T[] | ApiListResponse<T>) {
  return Array.isArray(payload) ? payload : payload.results;
}

async function expectApiListContains(
  request: APIRequestContext,
  token: string,
  path: string,
  expected: { id: number; label: string },
  labelForError: string
) {
  const payload = await apiGet<ApiNamedRecord[] | ApiListResponse<ApiNamedRecord>>(
    request,
    path,
    token
  );
  const rows = unwrapList(payload);
  const labels = rows.map((row) => row.name ?? row.title ?? `#${row.id}`);

  expect(
    rows.some((row) => row.id === expected.id),
    [
      `Seeded ${labelForError} was not returned by the student-visible API.`,
      `Expected: ${expected.label} (#${expected.id})`,
      `Path: ${path}`,
      `Available: ${labels.join(", ") || "none"}`
    ].join("\n")
  ).toBe(true);
}

async function expectStudentApiCanSeeSeededAcademics(
  request: APIRequestContext,
  token: string,
  seed: SeedPracticeWorkflowData
) {
  const subjectParams = new URLSearchParams({
    search: seed.names.subject,
    page_size: "100"
  });
  const classLevelParams = new URLSearchParams({
    search: seed.names.classLevel,
    page_size: "100"
  });
  const topicParams = new URLSearchParams({
    subject: String(seed.ids.subject),
    class_level: String(seed.ids.classLevel),
    search: seed.names.topic,
    page_size: "100"
  });

  await expectApiListContains(
    request,
    token,
    `academics/subjects/?${subjectParams}`,
    { id: seed.ids.subject, label: seed.names.subject },
    "subject"
  );
  await expectApiListContains(
    request,
    token,
    `academics/class-levels/?${classLevelParams}`,
    { id: seed.ids.classLevel, label: seed.names.classLevel },
    "class level"
  );
  await expectApiListContains(
    request,
    token,
    `academics/topics/?${topicParams}`,
    { id: seed.ids.topic, label: seed.names.topic },
    "topic"
  );
}

test.describe("seeded practice workflow setup", () => {
  test("creates minimum workflow data and exposes it to the generated student", async ({
    page,
    request
  }) => {
    test.setTimeout(120_000);

    const seed = await seedPracticeWorkflowData(request);

    const auth = await loginByApiAndStorage(
      page,
      request,
      seed.studentCredentials.email,
      seed.studentCredentials.password
    );

    await expectStudentApiCanSeeSeededAcademics(request, auth.tokens.access, seed);

    await page.goto("/student/practice");
    await expect(
      page.getByRole("heading", { name: /^Practice$/i })
    ).toBeVisible();

    const subjectSelect = page.getByLabel("Subject");
    await expectSelectHasOption(
      subjectSelect,
      seed.names.subject,
      `subject select for seed IDs ${JSON.stringify(seed.ids)}`
    );
    await subjectSelect.selectOption({ label: seed.names.subject });

    const classLevelSelect = page.getByLabel("Class level");
    await expectSelectHasOption(
      classLevelSelect,
      seed.names.classLevel,
      `class level select for seed IDs ${JSON.stringify(seed.ids)}`
    );
    await classLevelSelect.selectOption({ label: seed.names.classLevel });

    const topicSelect = page.getByLabel("Topic");
    await expectSelectHasOption(
      topicSelect,
      seed.names.topic,
      `topic select for seed IDs ${JSON.stringify(seed.ids)}`
    );
    await topicSelect.selectOption({ label: seed.names.topic });

    await expect(page.getByRole("button", { name: /^Start Practice$/i })).toBeEnabled();
  });
});
