import { api } from "@/lib/api";
import type { SchoolSetupStatus } from "@/types/schools";

export const getSchoolSetupStatus = (schoolId?: number | string) => {
  const query = schoolId ? `?school=${encodeURIComponent(String(schoolId))}` : "";
  return api.get<SchoolSetupStatus>(`/schools/setup-status/${query}`);
};
