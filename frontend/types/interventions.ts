export type InterventionCategory =
  | "academic_support"
  | "parent_contact"
  | "remedial_assignment"
  | "revision_class"
  | "attendance_followup"
  | "behavior_followup"
  | "other";

export type InterventionPriority = "low" | "medium" | "high" | "urgent";

export type InterventionStatus = "open" | "in_progress" | "resolved" | "closed";

export type InterventionSourceType =
  | "manual"
  | "weak_student"
  | "weak_topic"
  | "progress_report"
  | "remediation_plan"
  | "admin_intervention_dashboard";

export type InterventionNote = {
  id: number;
  intervention: number;
  author: number | null;
  author_name: string;
  note: string;
  is_internal: boolean;
  created_at: string;
  updated_at: string;
};

export type StudentIntervention = {
  id: number;
  school: number;
  school_name: string;
  student: number;
  student_name: string;
  student_email: string;
  student_admission_number: string | null;
  student_class_arm: string;
  created_by: number | null;
  created_by_name: string;
  assigned_to: number | null;
  assigned_to_name: string;
  title: string;
  description: string;
  category: InterventionCategory;
  priority: InterventionPriority;
  status: InterventionStatus;
  source_type: InterventionSourceType;
  source_assignment: number | null;
  source_assignment_title: string | null;
  source_subject: number | null;
  source_subject_name: string | null;
  source_topic: number | null;
  source_topic_title: string | null;
  source_class_arm: number | null;
  source_class_arm_name: string;
  due_date: string | null;
  completed_at: string | null;
  notes_count: number;
  notes?: InterventionNote[];
  created_at: string;
  updated_at: string;
};

export type StudentInterventionPayload = {
  student: number;
  title: string;
  description?: string;
  category?: InterventionCategory;
  priority?: InterventionPriority;
  status?: InterventionStatus;
  assigned_to?: number | null;
  due_date?: string | null;
  source_type?: InterventionSourceType;
  source_assignment?: number | null;
  source_subject?: number | null;
  source_topic?: number | null;
  source_class_arm?: number | null;
};

export type InterventionUpdatePayload = Partial<
  Omit<StudentInterventionPayload, "student">
>;

export type InterventionNotePayload = {
  note: string;
  is_internal?: boolean;
};

export type CreateInterventionFromProgressReportPayload = {
  student: number;
  title: string;
  description?: string;
  priority?: InterventionPriority;
  due_date?: string | null;
  recommended_action?: string;
  source_subject?: number | null;
  source_topic?: number | null;
  assigned_to?: number | null;
};

export type InterventionListParams = Record<
  string,
  string | number | boolean | null | undefined
>;
