export type ApiErrorPayload = {
  detail?: string;
  [key: string]: unknown;
};

export type NavItem = {
  label: string;
  href: string;
};

export type DashboardRole = "admin" | "teacher" | "student";

export type StatItem = {
  label: string;
  value: string | number;
  helper?: string;
};
