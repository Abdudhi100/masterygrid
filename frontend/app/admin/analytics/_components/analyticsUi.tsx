import { Badge } from "@/components/ui/Badge";

export type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

export function formatDate(value?: string | null) {
  if (!value) {
    return "Not set";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not set";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

export function formatPercentage(value: number) {
  return `${Number(value).toFixed(2)}%`;
}

export function humanize(value: string) {
  return value.replaceAll("_", " ");
}

export function scoreTone(percentage: number): BadgeTone {
  if (percentage >= 70) {
    return "success";
  }

  if (percentage >= 50) {
    return "warning";
  }

  return "danger";
}

export function riskTone(value: string): BadgeTone {
  if (value === "high") {
    return "danger";
  }

  if (value === "medium" || value === "warning" || value === "low_activity") {
    return "warning";
  }

  if (value === "low" || value === "good" || value === "active") {
    return "success";
  }

  if (value === "poor" || value === "inactive" || value === "archived") {
    return "danger";
  }

  if (value === "published") {
    return "success";
  }

  if (value === "draft") {
    return "warning";
  }

  return "neutral";
}

export function ScoreBadge({ percentage }: { percentage: number }) {
  const label =
    percentage >= 70 ? "strong" : percentage >= 50 ? "average" : "weak";

  return <Badge tone={scoreTone(percentage)}>{label}</Badge>;
}

export function StatusBadge({ value }: { value: string }) {
  return <Badge tone={riskTone(value)}>{humanize(value)}</Badge>;
}
