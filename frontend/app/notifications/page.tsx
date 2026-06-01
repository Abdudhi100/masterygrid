"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { NotificationList } from "@/components/notifications/NotificationList";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Select } from "@/components/ui/Select";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import { dashboardPathForRole } from "@/lib/routes";
import {
  archiveNotification,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead
} from "@/lib/notifications";
import type {
  Notification,
  NotificationPriority,
  NotificationStatus,
  NotificationType
} from "@/types/notifications";

export default function NotificationsPage() {
  const router = useRouter();
  const { user, status } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notificationStatus, setNotificationStatus] = useState<
    NotificationStatus | ""
  >("");
  const [priority, setPriority] = useState<NotificationPriority | "">("");
  const [notificationType, setNotificationType] = useState<NotificationType | "">(
    ""
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState("");

  const loadNotifications = useCallback(async () => {
    if (!user) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      setNotifications(
        await getNotifications({
          status: notificationStatus,
          priority,
          notification_type: notificationType,
          page_size: 100
        })
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to load notifications."
      );
    } finally {
      setIsLoading(false);
    }
  }, [notificationStatus, notificationType, priority, user]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login?next=%2Fnotifications");
    }
  }, [router, status]);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  async function handleOpen(notification: Notification) {
    if (notification.status === "unread") {
      await markNotificationRead(notification.id);
    }
    if (notification.target_url) {
      router.push(notification.target_url);
    } else {
      await loadNotifications();
    }
  }

  async function handleArchive(notification: Notification) {
    setIsUpdating(true);
    try {
      await archiveNotification(notification.id);
      await loadNotifications();
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleMarkAllRead() {
    setIsUpdating(true);
    try {
      await markAllNotificationsRead();
      await loadNotifications();
    } finally {
      setIsUpdating(false);
    }
  }

  if (status === "loading") {
    return (
      <main className="min-h-screen bg-surface p-6">
        <LoadingState label="Checking your session..." />
      </main>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-surface p-6">
        <LoadingState label="Redirecting..." />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-surface px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl" data-testid="notification-page">
        <PageHeader
          title="Notifications"
          description="Review assignment, submission, intervention, and system updates."
          actions={
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={handleMarkAllRead}
                isLoading={isUpdating}
                data-testid="notification-mark-all-read-button"
              >
                Mark All Read
              </Button>
              <Link href={dashboardPathForRole(user.role)}>
                <Button variant="secondary">Back to Dashboard</Button>
              </Link>
            </div>
          }
        />

        <Card>
          <div className="grid gap-4 md:grid-cols-3">
            <Select
              label="Status"
              value={notificationStatus}
              onChange={(event) =>
                setNotificationStatus(event.target.value as NotificationStatus | "")
              }
              options={[
                { value: "", label: "All statuses" },
                { value: "unread", label: "Unread" },
                { value: "read", label: "Read" },
                { value: "archived", label: "Archived" }
              ]}
            />
            <Select
              label="Priority"
              value={priority}
              onChange={(event) =>
                setPriority(event.target.value as NotificationPriority | "")
              }
              options={[
                { value: "", label: "All priorities" },
                { value: "urgent", label: "Urgent" },
                { value: "high", label: "High" },
                { value: "normal", label: "Normal" },
                { value: "low", label: "Low" }
              ]}
            />
            <Select
              label="Type"
              value={notificationType}
              onChange={(event) =>
                setNotificationType(event.target.value as NotificationType | "")
              }
              options={[
                { value: "", label: "All types" },
                { value: "assignment_published", label: "Assignment Published" },
                { value: "assignment_submitted", label: "Assignment Submitted" },
                { value: "intervention_created", label: "Intervention Created" },
                { value: "intervention_note_added", label: "Intervention Note Added" },
                { value: "learning_recommendation", label: "Learning Recommendation" },
                { value: "system", label: "System" }
              ]}
            />
          </div>
        </Card>

        <section className="mt-6">
          {isLoading ? (
            <LoadingState label="Loading notifications..." />
          ) : error ? (
            <EmptyState title="Notifications unavailable" description={error} />
          ) : (
            <NotificationList
              notifications={notifications}
              onOpen={handleOpen}
              onArchive={handleArchive}
            />
          )}
        </section>
      </div>
    </main>
  );
}
