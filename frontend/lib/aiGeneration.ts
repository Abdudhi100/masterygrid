import { api } from "@/lib/api";
import type { ListResponse } from "@/types/academics";
import type {
  AIQuestionSuggestionApplyPayload,
  AIQuestionSuggestionApplyResponse,
  AIQuestionSuggestionCreatePayload,
  AIQuestionSuggestionFilters,
  AIQuestionSuggestionRun
} from "@/types/aiGeneration";

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

export const createQuestionSuggestion = (data: AIQuestionSuggestionCreatePayload) =>
  api.post<AIQuestionSuggestionRun>("/ai-generation/question-suggestions/", data);

export const getQuestionSuggestions = async (
  params?: AIQuestionSuggestionFilters
) => {
  const payload = await api.get<
    AIQuestionSuggestionRun[] | ListResponse<AIQuestionSuggestionRun>
  >(`/ai-generation/question-suggestions/${queryString(params)}`);
  return unwrapList(payload);
};

export const getQuestionSuggestion = (id: number | string) =>
  api.get<AIQuestionSuggestionRun>(`/ai-generation/question-suggestions/${id}/`);

export const applyQuestionSuggestion = (
  id: number | string,
  fieldsToApply: AIQuestionSuggestionApplyPayload["fields_to_apply"]
) =>
  api.post<AIQuestionSuggestionApplyResponse>(
    `/ai-generation/question-suggestions/${id}/apply/`,
    { fields_to_apply: fieldsToApply }
  );
