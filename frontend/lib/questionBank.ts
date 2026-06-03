import { api } from "@/lib/api";
import type { ListResponse } from "@/types/academics";
import type {
  Question,
  QuestionBulkAction,
  QuestionBulkActionResponse,
  QuestionFilters,
  QuestionImportBatch,
  QuestionImportFilters,
  QuestionImportPreflightResponse,
  QuestionImportRow,
  QuestionQualityDashboard,
  QuestionQualityFilters,
  QuestionMedia,
  QuestionMediaPayload,
  QuestionPayload,
  QuestionSource,
  QuestionSourceFilters,
  QuestionSourcePayload
} from "@/types/questionBank";

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

export const getQuestionSources = async (params?: QuestionSourceFilters) => {
  const payload = await api.get<QuestionSource[] | ListResponse<QuestionSource>>(
    `/question-bank/sources/${queryString(params)}`
  );
  return unwrapList(payload);
};

export const createQuestionSource = (data: QuestionSourcePayload) =>
  api.post<QuestionSource>("/question-bank/sources/", data);

export const updateQuestionSource = (
  id: number | string,
  data: Partial<QuestionSourcePayload>
) => api.patch<QuestionSource>(`/question-bank/sources/${id}/`, data);

export const getQuestions = async (params?: QuestionFilters) => {
  const payload = await api.get<Question[] | ListResponse<Question>>(
    `/question-bank/questions/${queryString(params)}`
  );
  return unwrapList(payload);
};

export const getQuestion = (id: number | string) =>
  api.get<Question>(`/question-bank/questions/${id}/`);

export const createQuestion = (data: QuestionPayload) =>
  api.post<Question>("/question-bank/questions/", data);

export const updateQuestion = (
  id: number | string,
  data: Partial<QuestionPayload>
) => api.patch<Question>(`/question-bank/questions/${id}/`, data);

export const approveQuestion = (id: number | string) =>
  api.post<Question>(`/question-bank/questions/${id}/approve/`);

export const rejectQuestion = (id: number | string) =>
  api.post<Question>(`/question-bank/questions/${id}/reject/`);

export const archiveQuestion = (id: number | string) =>
  api.post<Question>(`/question-bank/questions/${id}/archive/`);

export const bulkQuestionAction = (
  questionIds: number[],
  action: QuestionBulkAction
) =>
  api.post<QuestionBulkActionResponse>("/question-bank/questions/bulk-action/", {
    question_ids: questionIds,
    action
  });

export const getQuestionQualityDashboard = (params?: QuestionQualityFilters) =>
  api.get<QuestionQualityDashboard>(
    `/question-bank/quality-dashboard/${queryString(params)}`
  );

export const getQuestionMedia = (questionId: number | string) =>
  api.get<QuestionMedia[]>(`/question-bank/questions/${questionId}/media/`);

export const createQuestionMedia = (
  questionId: number | string,
  payload: QuestionMediaPayload
) =>
  api.post<QuestionMedia>(
    `/question-bank/questions/${questionId}/media/`,
    payload
  );

export const updateQuestionMedia = (
  mediaId: number | string,
  payload: Partial<QuestionMediaPayload>
) => api.patch<QuestionMedia>(`/question-bank/media/${mediaId}/`, payload);

export const deleteQuestionMedia = (mediaId: number | string) =>
  api.delete<void>(`/question-bank/media/${mediaId}/`);

export const getQuestionImports = async (params?: QuestionImportFilters) => {
  const payload = await api.get<
    QuestionImportBatch[] | ListResponse<QuestionImportBatch>
  >(`/question-bank/imports/${queryString(params)}`);
  return unwrapList(payload);
};

export const getQuestionImport = (id: number | string) =>
  api.get<QuestionImportBatch>(`/question-bank/imports/${id}/`);

export const getQuestionImportRows = async (id: number | string) => {
  const payload = await api.get<
    QuestionImportRow[] | ListResponse<QuestionImportRow>
  >(`/question-bank/imports/${id}/rows/?page_size=100`);

  if (Array.isArray(payload)) {
    return payload;
  }

  const rows = [...payload.results];
  let page = 2;
  while (payload.count > rows.length) {
    const pagePayload = await api.get<ListResponse<QuestionImportRow>>(
      `/question-bank/imports/${id}/rows/?page_size=100&page=${page}`
    );
    rows.push(...pagePayload.results);
    if (!pagePayload.next) {
      break;
    }
    page += 1;
  }

  return rows;
};

export const createQuestionImport = (formData: FormData) =>
  api.post<QuestionImportBatch>("/question-bank/imports/", formData);

export const preflightQuestionImport = (formData: FormData) =>
  api.post<QuestionImportPreflightResponse>(
    "/question-bank/imports/preflight/",
    formData
  );
