import type { AssignmentDeadlineStatus } from "@/types/academics";

export type DeadlineBadgeTone =
  | "neutral"
  | "success"
  | "warning"
  | "danger"
  | "brand";

export function formatDeadlineStatus(status?: AssignmentDeadlineStatus | string | null) {
  if (!status) {
    return "Not set";
  }
  if (status === "late_open") {
    return "Late submission allowed";
  }
  if (status === "due_soon") {
    return "Due soon";
  }
  return status.replaceAll("_", " ");
}

export function deadlineStatusTone(
  status?: AssignmentDeadlineStatus | string | null
): DeadlineBadgeTone {
  if (status === "graded" || status === "submitted" || status === "open") {
    return "success";
  }
  if (status === "due_soon" || status === "scheduled" || status === "late_open") {
    return "warning";
  }
  if (status === "overdue" || status === "closed") {
    return "danger";
  }
  return "neutral";
}
