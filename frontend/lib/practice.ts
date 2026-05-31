import { api } from "@/lib/api";
import type { ListResponse, QueryParams } from "@/types/academics";
import type {
  PracticeAnswerInput,
  PracticeAnalyticsDashboard,
  PracticeRecommendation,
  PracticeResult,
  PracticeSession,
  PracticeStartPayload,
  PracticeSubjectPerformance,
  PracticeSummary,
  PracticeTopicPerformance,
  StudentLearningPath
} from "@/types/practice";

function unwrapList<T>(payload: T[] | ListResponse<T>) {
  return Array.isArray(payload) ? payload : payload.results;
}

function queryString(params?: QueryParams) {
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

export const startPracticeSession = (data: PracticeStartPayload) =>
  api.post<PracticeSession>("/practice/sessions/start/", data);

export const getPracticeSessions = async (params?: QueryParams) => {
  const payload = await api.get<PracticeSession[] | ListResponse<PracticeSession>>(
    `/practice/sessions/${queryString(params)}`
  );
  return unwrapList(payload);
};

export const getPracticeSession = (id: number | string) =>
  api.get<PracticeSession>(`/practice/sessions/${id}/`);

export const submitPracticeSession = (
  id: number | string,
  answers: PracticeAnswerInput[]
) =>
  api.post<PracticeResult>(`/practice/sessions/${id}/submit/`, {
    answers
  });

export const getPracticeResult = (id: number | string) =>
  api.get<PracticeResult>(`/practice/sessions/${id}/result/`);

export const getPracticeAnalyticsSummary = () =>
  api.get<PracticeSummary>("/practice/analytics/summary/");

export const getPracticeSubjectPerformance = () =>
  api.get<PracticeSubjectPerformance[]>("/practice/analytics/subjects/");

export const getPracticeTopicPerformance = () =>
  api.get<PracticeTopicPerformance[]>("/practice/analytics/topics/");

export const getPracticeWeakTopics = () =>
  api.get<PracticeTopicPerformance[]>("/practice/analytics/weak-topics/");

export const getPracticeStrongTopics = () =>
  api.get<PracticeTopicPerformance[]>("/practice/analytics/strong-topics/");

export const getPracticeRecommendations = () =>
  api.get<PracticeRecommendation[]>("/practice/analytics/recommendations/");

export const getPracticeAnalyticsDashboard = () =>
  api.get<PracticeAnalyticsDashboard>("/practice/analytics/dashboard/");

export const getPracticeLearningPath = () =>
  api.get<StudentLearningPath>("/practice/learning-path/");
