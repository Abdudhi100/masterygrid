import { api } from "@/lib/api";
import type { ListResponse } from "@/types/academics";
import type { AuditLog, AuditLogFilters } from "@/types/audit";

function queryString(params?: Record<string, string | number | boolean | null | undefined>) {
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

export const getAuditLogs = (params?: AuditLogFilters) =>
  api.get<ListResponse<AuditLog>>(
    `/audit/logs/${queryString({ page_size: 50, ...params })}`
  );

export const getAuditLog = (id: number | string) =>
  api.get<AuditLog>(`/audit/logs/${id}/`);
