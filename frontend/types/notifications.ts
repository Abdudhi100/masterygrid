export type NotificationType =
  | "assignment_published"
  | "assignment_due_soon"
  | "assignment_deadline_extended"
  | "assignment_reopened"
  | "assignment_submitted"
  | "low_submission_rate"
  | "weak_topic_detected"
  | "intervention_created"
  | "intervention_updated"
  | "intervention_note_added"
  | "intervention_due"
  | "progress_report_available"
  | "learning_recommendation"
  | "system";

export type NotificationPriority = "low" | "normal" | "high" | "urgent";

export type NotificationStatus = "unread" | "read" | "archived";

export type Notification = {
  id: number;
  school: number | null;
  school_name: string | null;
  recipient: number;
  recipient_name: string;
  actor: number | null;
  actor_name: string | null;
  title: string;
  message: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  status: NotificationStatus;
  target_url: string;
  object_type: string;
  object_id: string;
  metadata: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
  updated_at: string;
};

export type NotificationListParams = Record<
  string,
  string | number | boolean | null | undefined
>;

export type UnreadNotificationCount = {
  unread_count: number;
};
