export type BulkImportType =
  | "students"
  | "teachers"
  | "student_enrollments"
  | "teacher_assignments";

export type BulkImportDomain = "accounts" | "academics";

export type BulkImportBatchStatus =
  | "pending"
  | "processing"
  | "completed"
  | "completed_with_errors"
  | "failed";

export type BulkImportRowStatus =
  | "pending"
  | "imported"
  | "failed"
  | "warning"
  | "duplicate";

export type BulkImportPreflightRowStatus =
  | "valid"
  | "valid_with_warnings"
  | "invalid"
  | "duplicate";

export type BulkImportIssue = {
  field: string;
  message: string;
};

export type BulkImportPreflightRow = {
  row_number: number;
  status: BulkImportPreflightRowStatus;
  errors: BulkImportIssue[];
  warnings: BulkImportIssue[];
  duplicate_type: "in_file" | "database" | "";
  raw_data?: Record<string, string>;
  full_name?: string;
  email?: string;
  identifier?: string;
  student?: string;
  teacher?: string;
  class_arm?: string;
  subject?: string;
  academic_session?: string;
  term?: string;
  resolved?: Record<string, string | number | null>;
};

export type BulkImportPreflightSummary = {
  missing_required_fields?: number;
  invalid_emails?: number;
  duplicate_emails?: number;
  existing_emails?: number;
  duplicate_identifiers?: number;
  existing_identifiers?: number;
  missing_class_arms?: string[];
  missing_students?: number;
  missing_teachers?: number;
  missing_subjects?: string[];
  missing_academic_sessions?: string[];
  missing_terms?: string[];
  duplicate_rows?: number;
  existing_records?: number;
};

export type BulkImportPreflightResponse = {
  import_type: BulkImportType;
  file_type: "csv";
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  warning_rows: number;
  duplicate_rows: number;
  can_import: boolean;
  summary: BulkImportPreflightSummary;
  rows: BulkImportPreflightRow[];
};

export type BulkImportBatch = {
  id: number;
  school: number;
  school_name?: string;
  uploaded_by: number;
  uploaded_by_name?: string;
  import_type: BulkImportType;
  original_filename: string;
  status: BulkImportBatchStatus;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  warning_rows: number;
  error_message: string;
  created_at: string;
  updated_at: string;
  domain?: BulkImportDomain;
};

export type BulkImportRow = {
  id: number;
  batch: number;
  row_number: number;
  status: BulkImportRowStatus;
  raw_data: Record<string, string>;
  error_message: string;
  warning_message: string;
  user?: number | null;
  user_name?: string;
  user_email?: string;
  student_enrollment?: number | null;
  student_enrollment_display?: string;
  teacher_assignment?: number | null;
  teacher_assignment_display?: string;
};
