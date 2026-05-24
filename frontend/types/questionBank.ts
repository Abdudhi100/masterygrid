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

export type QuestionMedia = {
  id: number;
  media_type: "image";
  image: string | null;
  image_url: string;
  external_url: string;
  original_filename: string;
  description: string;
  alt_text: string;
  caption: string;
  display_order: number;
  is_primary: boolean;
  is_active: boolean;
  needs_manual_review: boolean;
  created_at?: string;
  updated_at?: string;
};

export type QuestionMediaPayload = {
  external_url?: string;
  description?: string;
  alt_text?: string;
  caption?: string;
  is_primary?: boolean;
  needs_manual_review?: boolean;
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
  content_hash?: string;
  difficulty: QuestionDifficulty;
  status: QuestionStatus;
  created_by: number | null;
  created_by_name?: string | null;
  reviewed_by: number | null;
  reviewed_by_name?: string | null;
  reviewed_at: string | null;
  is_active: boolean;
  has_diagram: boolean;
  diagram_description: string;
  needs_manual_review: boolean;
  is_usable_for_assignment?: boolean;
  options: QuestionOption[];
  media: QuestionMedia[];
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
  has_diagram?: boolean;
  diagram_description?: string;
  needs_manual_review?: boolean;
  media?: QuestionMediaPayload[];
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

export type QuestionImportStatus =
  | "uploaded"
  | "processing"
  | "completed"
  | "completed_with_errors"
  | "failed";

export type QuestionImportRowStatus =
  | "pending"
  | "imported"
  | "failed"
  | "duplicate";

export type QuestionImportFileType = "csv" | "xlsx" | "json" | "zip";

export type QuestionImportBatch = {
  id: number;
  school: number | null;
  school_name?: string | null;
  uploaded_by: number;
  uploaded_by_name?: string | null;
  source: number | null;
  source_name?: string | null;
  title: string;
  original_filename: string;
  file_type: QuestionImportFileType;
  status: QuestionImportStatus;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  warning_rows?: number;
  error_summary: string;
  created_at?: string;
  updated_at?: string;
  processed_at: string | null;
};

export type QuestionImportRow = {
  id: number;
  batch: number;
  row_number: number;
  raw_data: Record<string, unknown>;
  status: QuestionImportRowStatus;
  error_message: string;
  warning_message?: string;
  question: number | null;
  question_text?: string | null;
  content_hash: string;
  created_at?: string;
  updated_at?: string;
};

export type QuestionImportFilters = QueryParams & {
  status?: QuestionImportStatus | "";
  search?: string;
};

export type QuestionImportPreflightIssue = {
  field: string;
  message: string;
};

export type QuestionImportPreflightError = QuestionImportPreflightIssue;

export type QuestionImportPreflightWarning = QuestionImportPreflightIssue;

export type QuestionImportPreflightRowStatus =
  | "valid"
  | "valid_with_warnings"
  | "invalid"
  | "duplicate";

export type QuestionImportPreflightDuplicateType =
  | "in_file"
  | "database"
  | "";

export type QuestionImportPreflightResolved = {
  subject_id: number | null;
  subject_name: string;
  class_level_id: number | null;
  class_level_name: string;
  topic_id: number | null;
  topic_title: string;
};

export type QuestionImportPreflightRow = {
  row_number: number;
  status: QuestionImportPreflightRowStatus;
  errors: QuestionImportPreflightError[];
  warnings: QuestionImportPreflightWarning[];
  duplicate_type: QuestionImportPreflightDuplicateType;
  content_hash: string;
  question_preview: string;
  subject: string;
  class_level: string;
  topic: string;
  diagram_file_name: string;
  resolved: QuestionImportPreflightResolved;
};

export type QuestionImportPreflightSummary = {
  missing_required_fields: number;
  missing_correct_option: number;
  missing_options: number;
  invalid_difficulty: number;
  invalid_correct_option: number;
  invalid_source_type: number;
  duplicate_option_texts: number;
  missing_subjects: string[];
  missing_class_levels: string[];
  missing_topics: string[];
  missing_diagrams: number;
  duplicate_questions: number;
  existing_database_duplicates: number;
};

export type QuestionImportPreflightResponse = {
  file_type: QuestionImportFileType;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  warning_rows: number;
  duplicate_rows: number;
  can_import: boolean;
  summary: QuestionImportPreflightSummary;
  rows: QuestionImportPreflightRow[];
};
