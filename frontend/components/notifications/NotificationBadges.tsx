"use client";

import { Badge } from "@/components/ui/Badge";
import type {
  NotificationPriority,
  NotificationStatus
} from "@/types/notifications";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "brand";

export function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function priorityTone(priority: NotificationPriority): BadgeTone {
  if (priority === "urgent" || priority === "high") {
    return "danger";
  }
  if (priority === "normal") {
    return "brand";
  }
  return "neutral";
}

function statusTone(status: NotificationStatus): BadgeTone {
  if (status === "unread") {
    return "brand";
  }
  if (status === "read") {
    return "success";
  }
  return "neutral";
}

export function NotificationPriorityBadge({
  priority
}: {
  priority: NotificationPriority;
}) {
  return <Badge tone={priorityTone(priority)}>{titleCase(priority)}</Badge>;
}

export function NotificationStatusBadge({
  status
}: {
  status: NotificationStatus;
}) {
  return <Badge tone={statusTone(status)}>{titleCase(status)}</Badge>;
}
