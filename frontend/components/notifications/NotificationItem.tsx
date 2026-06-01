"use client";

import {
  NotificationPriorityBadge,
  NotificationStatusBadge,
  titleCase
} from "@/components/notifications/NotificationBadges";
import { Button } from "@/components/ui/Button";
import type { Notification } from "@/types/notifications";

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

export function NotificationItem({
  notification,
  onOpen,
  onArchive,
  compact = false
}: {
  notification: Notification;
  onOpen: (notification: Notification) => void;
  onArchive?: (notification: Notification) => void;
  compact?: boolean;
}) {
  return (
    <div
      className={`rounded-md border border-line bg-white p-4 ${
        notification.status === "unread" ? "ring-1 ring-brand-100" : ""
      }`}
      data-testid="notification-item"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <NotificationStatusBadge status={notification.status} />
            <NotificationPriorityBadge priority={notification.priority} />
            {!compact ? (
              <span className="text-xs font-semibold text-muted">
                {titleCase(notification.notification_type)}
              </span>
            ) : null}
          </div>
          <h3
            className="mt-3 font-semibold text-ink"
            data-testid="notification-title"
          >
            {notification.title}
          </h3>
          {notification.message ? (
            <p className="mt-2 text-sm leading-6 text-muted">
              {notification.message}
            </p>
          ) : null}
          <p className="mt-2 text-xs font-semibold text-muted">
            {formatDate(notification.created_at)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpen(notification)}
          >
            Open
          </Button>
          {onArchive ? (
            <Button
              type="button"
              variant="ghost"
              onClick={() => onArchive(notification)}
              data-testid="notification-archive-button"
            >
              Archive
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
