import { api } from "@/lib/api";
import type { ListResponse } from "@/types/academics";
import type {
  CreateInterventionFromProgressReportPayload,
  InterventionListParams,
  InterventionNote,
  InterventionNotePayload,
  InterventionUpdatePayload,
  StudentIntervention,
  StudentInterventionPayload
} from "@/types/interventions";

function unwrapList<T>(payload: T[] | ListResponse<T>) {
  return Array.isArray(payload) ? payload : payload.results;
}

function queryString(params?: InterventionListParams) {
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

export const getInterventions = async (params?: InterventionListParams) => {
  const payload = await api.get<StudentIntervention[] | ListResponse<StudentIntervention>>(
    `/interventions/${queryString(params)}`
  );
  return unwrapList(payload);
};

export const getIntervention = (id: number | string) =>
  api.get<StudentIntervention>(`/interventions/${id}/`);

export const createIntervention = (payload: StudentInterventionPayload) =>
  api.post<StudentIntervention>("/interventions/", payload);

export const updateIntervention = (
  id: number | string,
  payload: InterventionUpdatePayload
) => api.patch<StudentIntervention>(`/interventions/${id}/`, payload);

export const addInterventionNote = (
  id: number | string,
  payload: InterventionNotePayload
) => api.post<InterventionNote>(`/interventions/${id}/add-note/`, payload);

export const getStudentInterventions = (studentId: number | string) =>
  api.get<StudentIntervention[]>(`/interventions/student/${studentId}/`);

export const createInterventionFromProgressReport = (
  payload: CreateInterventionFromProgressReportPayload
) =>
  api.post<StudentIntervention>(
    "/interventions/create-from-progress-report/",
    payload
  );
