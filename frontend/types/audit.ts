export type AuditCategory =
  | "auth"
  | "academics"
  | "question_bank"
  | "assignment"
  | "submission"
  | "intervention"
  | "notification"
  | "import"
  | "user_management"
  | "system";

export type AuditLog = {
  id: number;
  school: number | null;
  school_name: string;
  actor: number | null;
  actor_name: string;
  actor_email: string;
  actor_role: string;
  action: string;
  category: AuditCategory;
  object_type: string;
  object_id: string;
  object_repr: string;
  target_user: number | null;
  target_user_name: string;
  target_user_email: string;
  ip_address: string | null;
  user_agent: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AuditLogFilters = {
  category?: AuditCategory | "";
  action?: string;
  actor?: number | string;
  target_user?: number | string;
  object_type?: string;
  date_from?: string;
  date_to?: string;
  school?: number | string;
  search?: string;
};
