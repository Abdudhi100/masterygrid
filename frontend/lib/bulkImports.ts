import { api } from "@/lib/api";
import type { ListResponse } from "@/types/academics";
import type {
  BulkImportBatch,
  BulkImportDomain,
  BulkImportPreflightResponse,
  BulkImportRow,
  BulkImportType
} from "@/types/bulkImports";

function unwrapList<T>(payload: T[] | ListResponse<T>) {
  return Array.isArray(payload) ? payload : payload.results;
}

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

export function domainForImportType(importType: BulkImportType): BulkImportDomain {
  return importType === "students" || importType === "teachers"
    ? "accounts"
    : "academics";
}

function basePath(domain: BulkImportDomain) {
  return domain === "accounts" ? "/auth/imports" : "/academics/imports";
}

export const preflightBulkImport = (
  domain: BulkImportDomain,
  formData: FormData
) =>
  api.post<BulkImportPreflightResponse>(
    `${basePath(domain)}/preflight/`,
    formData
  );

export const createBulkImport = (
  domain: BulkImportDomain,
  formData: FormData
) => api.post<BulkImportBatch>(`${basePath(domain)}/`, formData);

export const getBulkImports = async (
  domain: BulkImportDomain,
  params?: { import_type?: BulkImportType }
) => {
  const payload = await api.get<BulkImportBatch[] | ListResponse<BulkImportBatch>>(
    `${basePath(domain)}/${queryString(params)}`
  );
  return unwrapList(payload).map((item) => ({ ...item, domain }));
};

export const getAllBulkImports = async () => {
  const [accountImports, academicImports] = await Promise.all([
    getBulkImports("accounts"),
    getBulkImports("academics")
  ]);
  return [...accountImports, ...academicImports].sort((a, b) =>
    b.created_at.localeCompare(a.created_at)
  );
};

export const getBulkImport = (domain: BulkImportDomain, id: number | string) =>
  api.get<BulkImportBatch>(`${basePath(domain)}/${id}/`);

export const getBulkImportRows = (domain: BulkImportDomain, id: number | string) =>
  api.get<BulkImportRow[]>(`${basePath(domain)}/${id}/rows/`);
