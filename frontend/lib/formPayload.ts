import type { FormState } from "@/components/admin/ResourceForm";

export function numberOrNull(value: string | boolean | undefined) {
  if (typeof value !== "string" || value === "") {
    return null;
  }
  return Number(value);
}

export function numberValue(value: string | boolean | undefined) {
  return Number(value);
}

export function stringValue(value: string | boolean | undefined) {
  return typeof value === "string" ? value : "";
}

export function booleanValue(value: string | boolean | undefined) {
  return Boolean(value);
}

export function tagsFromCsv(value: string | boolean | undefined) {
  if (typeof value !== "string") {
    return [];
  }

  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function csvFromTags(tags: string[] | undefined) {
  return tags?.join(", ") ?? "";
}

export function activeInitial(extra: FormState = {}): FormState {
  return {
    is_active: true,
    ...extra
  };
}
