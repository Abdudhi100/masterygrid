import type { QueryParams } from "@/types/academics";

export type QuestionStatus = "draft" | "approved" | "rejected" | "archived";

export type QuestionDifficulty = "easy" | "medium" | "hard";

export type QuestionSourceType =
  | "jamb_past_question"
  | "waec_past_question"
  | "neco_past_question"
  | "teacher_created"
  | "ai_generated"
  | "school_created";

export type QuestionOptionLabel = "A" | "B" | "C" | "D";

export type QuestionSource = {
  id: number;
  name: string;
  source_type: QuestionSourceType;
  exam_body: string;
  year: number | null;
  description: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type QuestionOption = {
  id?: number;
  label: QuestionOptionLabel;
  text: string;
  is_correct: boolean;
  created_at?: string;
  updated_at?: string;
};

export type Question = {
  id: number;
  school: number | null;
  school_name?: string | null;
  subject: number;
  subject_name?: string;
  topic: number;
  topic_title?: string;
  class_level: number;
  class_level_name?: string;
  source: number | null;
  source_name?: string | null;
  source_type?: QuestionSourceType | null;
  question_text: string;
  explanation: string;
  difficulty: QuestionDifficulty;
  status: QuestionStatus;
  created_by: number | null;
  created_by_name?: string | null;
  reviewed_by: number | null;
  reviewed_by_name?: string | null;
  reviewed_at: string | null;
  is_active: boolean;
  is_usable_for_assignment?: boolean;
  options: QuestionOption[];
  created_at?: string;
  updated_at?: string;
};

export type QuestionPayload = {
  subject: number;
  topic: number;
  class_level: number;
  source?: number | null;
  question_text: string;
  explanation?: string;
  difficulty: QuestionDifficulty;
  options: QuestionOption[];
};

export type QuestionFilters = QueryParams & {
  subject?: number | string;
  topic?: number | string;
  class_level?: number | string;
  difficulty?: QuestionDifficulty | "";
  status?: QuestionStatus | "";
  source?: number | string;
  source_type?: QuestionSourceType | "";
  search?: string;
};

export type QuestionSourcePayload = {
  name: string;
  source_type: QuestionSourceType;
  exam_body?: string;
  year?: number | null;
  description?: string;
  is_active?: boolean;
};

export type QuestionSourceFilters = QueryParams & {
  source_type?: QuestionSourceType | "";
  exam_body?: string;
  year?: number | string;
  is_active?: boolean | string;
  search?: string;
};
