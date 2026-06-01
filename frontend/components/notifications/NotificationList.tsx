"use client";

import { NotificationItem } from "@/components/notifications/NotificationItem";
import { EmptyState } from "@/components/ui/EmptyState";
import type { Notification } from "@/types/notifications";

export function NotificationList({
  notifications,
  onOpen,
  onArchive
}: {
  notifications: Notification[];
  onOpen: (notification: Notification) => void;
  onArchive: (notification: Notification) => void;
}) {
  if (!notifications.length) {
    return (
      <EmptyState
        title="No notifications"
        description="Notifications matching your filters will appear here."
      />
    );
  }

  return (
    <div className="space-y-3">
      {notifications.map((notification) => (
        <div key={notification.id} data-testid="notification-row">
          <NotificationItem
            notification={notification}
            onOpen={onOpen}
            onArchive={onArchive}
          />
        </div>
      ))}
    </div>
  );
}
