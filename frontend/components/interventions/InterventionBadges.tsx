"use client";

import { Badge } from "@/components/ui/Badge";
import type {
  InterventionCategory,
  InterventionPriority,
  InterventionStatus
} from "@/types/interventions";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

export function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function priorityTone(priority: InterventionPriority): BadgeTone {
  if (priority === "urgent" || priority === "high") {
    return "danger";
  }
  if (priority === "medium") {
    return "warning";
  }
  return "neutral";
}

export function statusTone(status: InterventionStatus): BadgeTone {
  if (status === "resolved" || status === "closed") {
    return "success";
  }
  if (status === "in_progress") {
    return "warning";
  }
  return "brand";
}

export function categoryTone(category: InterventionCategory): BadgeTone {
  if (category === "parent_contact" || category === "attendance_followup") {
    return "warning";
  }
  if (category === "remedial_assignment" || category === "revision_class") {
    return "brand";
  }
  return "neutral";
}

export function InterventionPriorityBadge({
  priority
}: {
  priority: InterventionPriority;
}) {
  return <Badge tone={priorityTone(priority)}>{titleCase(priority)}</Badge>;
}

export function InterventionStatusBadge({
  status
}: {
  status: InterventionStatus;
}) {
  return <Badge tone={statusTone(status)}>{titleCase(status)}</Badge>;
}

export function InterventionCategoryBadge({
  category
}: {
  category: InterventionCategory;
}) {
  return <Badge tone={categoryTone(category)}>{titleCase(category)}</Badge>;
}
