export const APP_NAME = "MasteryGrid";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export const ACCESS_TOKEN_KEY = "masterygrid.access_token";
export const REFRESH_TOKEN_KEY = "masterygrid.refresh_token";

export const ROLE_LABELS = {
  platform_admin: "Platform Admin",
  school_admin: "School Admin",
  teacher: "Teacher",
  student: "Student"
} as const;
