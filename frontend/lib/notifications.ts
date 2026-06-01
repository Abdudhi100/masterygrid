import { api } from "@/lib/api";
import type { ListResponse } from "@/types/academics";
import type {
  Notification,
  NotificationListParams,
  UnreadNotificationCount
} from "@/types/notifications";

function unwrapList<T>(payload: T[] | ListResponse<T>) {
  return Array.isArray(payload) ? payload : payload.results;
}

function queryString(params?: NotificationListParams) {
  if (!params) {
    return "";
  }

  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export const getNotifications = async (params?: NotificationListParams) => {
  const payload = await api.get<Notification[] | ListResponse<Notification>>(
    `/notifications/${queryString(params)}`
  );
  return unwrapList(payload);
};

export const getUnreadNotificationCount = () =>
  api.get<UnreadNotificationCount>("/notifications/unread-count/");

export const markNotificationRead = (id: number | string) =>
  api.post<Notification>(`/notifications/${id}/mark-read/`);

export const markNotificationUnread = (id: number | string) =>
  api.post<Notification>(`/notifications/${id}/mark-unread/`);

export const archiveNotification = (id: number | string) =>
  api.post<Notification>(`/notifications/${id}/archive/`);

export const markAllNotificationsRead = () =>
  api.post<{ updated_count: number }>("/notifications/mark-all-read/");
