"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { NotificationItem } from "@/components/notifications/NotificationItem";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead
} from "@/lib/notifications";
import type { Notification } from "@/types/notifications";

export function NotificationBell() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const [recent, count] = await Promise.all([
        getNotifications({ page_size: 5 }),
        getUnreadNotificationCount()
      ]);
      setNotifications(recent.slice(0, 5));
      setUnreadCount(count.unread_count);
    } catch {
      setNotifications([]);
      setUnreadCount(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  useEffect(() => {
    function handleClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleOpen(notification: Notification) {
    if (notification.status === "unread") {
      await markNotificationRead(notification.id);
    }
    setUnreadCount((count) => Math.max(0, count - 1));
    setIsOpen(false);
    if (notification.target_url) {
      router.push(notification.target_url);
    } else {
      router.push("/notifications");
    }
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => {
          setIsOpen((current) => !current);
          void loadNotifications();
        }}
        className="relative inline-flex min-h-10 items-center justify-center rounded-md border border-line bg-white px-3 text-sm font-semibold text-ink shadow-sm transition hover:bg-surface focus:outline-none focus:ring-4 focus:ring-brand-100"
        data-testid="notification-bell"
        aria-label="Notifications"
      >
        Notifications
        {unreadCount > 0 ? (
          <span
            className="ml-2 rounded-full bg-danger px-2 py-0.5 text-xs font-bold text-white"
            data-testid="notification-unread-count"
          >
            {unreadCount}
          </span>
        ) : null}
      </button>

      {isOpen ? (
        <div
          className="absolute right-0 z-40 mt-2 w-[min(24rem,calc(100vw-2rem))] rounded-lg border border-line bg-white p-3 shadow-lg"
          data-testid="notification-dropdown"
        >
          <div className="flex items-center justify-between gap-3">
            <p className="font-semibold text-ink">Recent Notifications</p>
            <Link href="/notifications" onClick={() => setIsOpen(false)}>
              <Button variant="ghost">View All</Button>
            </Link>
          </div>

          <div className="mt-3 max-h-96 space-y-3 overflow-y-auto">
            {isLoading ? (
              <LoadingState label="Loading notifications..." />
            ) : notifications.length ? (
              notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onOpen={handleOpen}
                  compact
                />
              ))
            ) : (
              <EmptyState
                title="No notifications"
                description="Important updates will appear here."
              />
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
