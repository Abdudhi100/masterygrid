import { expect, type Locator } from "@playwright/test";

export async function readSelectOptions(select: Locator) {
  return select.locator("option").evaluateAll((options) =>
    options
      .map((option) => option.textContent?.trim())
      .filter((text): text is string => Boolean(text))
  );
}

export async function expectSelectHasOption(
  select: Locator,
  expectedLabel: string,
  context: string
) {
  try {
    await expect
      .poll(() => readSelectOptions(select), {
        timeout: 15_000,
        message: `Waiting for ${context} option "${expectedLabel}"`
      })
      .toContain(expectedLabel);
  } catch (error) {
    const availableOptions = await readSelectOptions(select);
    throw new Error(
      [
        `Expected ${context} option was not available.`,
        `Expected: ${expectedLabel}`,
        `Available options: ${availableOptions.join(", ") || "none"}`,
        `Original error: ${error instanceof Error ? error.message : String(error)}`
      ].join("\n")
    );
  }
}
