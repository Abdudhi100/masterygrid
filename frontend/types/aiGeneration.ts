import type { QueryParams } from "@/types/academics";
import type { QuestionDifficulty } from "@/types/questionBank";

export type AISuggestionType =
  | "topic_difficulty_explanation"
  | "explanation_only"
  | "difficulty_only"
  | "duplicate_quality_check";

export type AISuggestionStatus =
  | "pending"
  | "processing"
  | "succeeded"
  | "failed";

export type AIQuestionSuggestionRun = {
  id: number;
  school: number | null;
  school_name?: string | null;
  requested_by: number;
  requested_by_name?: string | null;
  question: number;
  question_text?: string;
  question_subject?: string;
  question_topic?: string;
  question_class_level?: string;
  current_topic?: number | null;
  current_topic_title?: string | null;
  current_difficulty?: QuestionDifficulty | null;
  current_explanation?: string | null;
  suggestion_type: AISuggestionType;
  status: AISuggestionStatus;
  provider: string;
  model_name: string;
  prompt_version?: string;
  suggested_topic: number | null;
  suggested_topic_title?: string | null;
  suggested_difficulty: QuestionDifficulty | null;
  suggested_explanation: string;
  duplicate_warning: string;
  quality_warning: string;
  confidence_score: number | null;
  raw_response?: unknown;
  error_message: string;
  applied_by: number | null;
  applied_by_name?: string | null;
  applied_at: string | null;
  completed_at: string | null;
  created_at?: string;
  updated_at?: string;
};

export type AIQuestionSuggestionCreatePayload = {
  question: number;
  suggestion_type: AISuggestionType;
};

export type AIQuestionSuggestionApplyPayload = {
  fields_to_apply: Array<"topic" | "difficulty" | "explanation">;
};

export type AIQuestionSuggestionApplyResponse = {
  question: unknown;
  applied_fields: string[];
  run: AIQuestionSuggestionRun;
};

export type AIQuestionSuggestionFilters = QueryParams & {
  status?: AISuggestionStatus | "";
  suggestion_type?: AISuggestionType | "";
  question?: number | string;
  school?: number | string;
};
