import type { CurrentUser } from "@/types/auth";

export type ListResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type AcademicSession = {
  id: number;
  school?: number;
  school_name?: string;
  name: string;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type Term = {
  id: number;
  school?: number;
  school_name?: string;
  academic_session: number;
  academic_session_name?: string;
  term_name?: string;
  name: "first" | "second" | "third";
  starts_at: string;
  ends_at: string;
  is_active: boolean;
};

export type ClassLevel = {
  id: number;
  school?: number;
  school_name?: string;
  name: string;
  description: string;
  is_active: boolean;
};

export type ClassArm = {
  id: number;
  school?: number;
  school_name?: string;
  class_level: number;
  class_level_name?: string;
  name: string;
  display_name?: string;
  description: string;
  is_active: boolean;
};

export type Subject = {
  id: number;
  school?: number | null;
  school_name?: string | null;
  scope?: "global" | "school";
  name: string;
  code: string;
  description: string;
  is_jamb_subject: boolean;
  is_active: boolean;
};

export type Topic = {
  id: number;
  school?: number | null;
  school_name?: string | null;
  scope?: "global" | "school";
  subject: number;
  subject_name?: string;
  class_level: number;
  class_level_name?: string;
  title: string;
  description: string;
  curriculum_tags: string[];
  jamb_relevance_level: "low" | "medium" | "high";
  is_active: boolean;
};

export type TeacherAssignment = {
  id: number;
  school?: number;
  school_name?: string;
  teacher: number;
  teacher_name?: string;
  teacher_email?: string;
  class_arm: number;
  class_arm_name?: string;
  subject: number;
  subject_name?: string;
  academic_session: number | null;
  academic_session_name?: string | null;
  term: number | null;
  term_name?: string | null;
  is_active: boolean;
};

export type StudentEnrollment = {
  id: number;
  school?: number;
  school_name?: string;
  student: number;
  student_name?: string;
  student_email?: string;
  class_arm: number;
  class_arm_name?: string;
  academic_session: number;
  academic_session_name?: string;
  term: number | null;
  term_name?: string | null;
  is_active: boolean;
};

export type LessonLog = {
  id: number;
  school?: number;
  school_name?: string;
  teacher?: number;
  teacher_name?: string;
  teacher_email?: string;
  class_arm: number;
  class_arm_name?: string;
  subject: number;
  subject_name?: string;
  topic: number;
  topic_title?: string;
  academic_session: number | null;
  academic_session_name?: string | null;
  term: number | null;
  term_name?: string | null;
  taught_at: string;
  notes: string;
  can_generate_assignment: boolean;
  created_at?: string;
  updated_at?: string;
};

export type LessonLogPayload = {
  class_arm: number;
  subject: number;
  topic: number;
  academic_session?: number | null;
  term?: number | null;
  taught_at: string;
  notes?: string;
};

export type User = CurrentUser;

export type TeacherProfileSummary = {
  id: number;
  staff_id: string;
  phone_number: string;
};

export type StudentProfileSummary = {
  id: number;
  admission_number: string;
  guardian_name: string;
  guardian_phone: string;
};

export type Teacher = {
  id: number;
  full_name: string;
  email: string;
  role: "teacher";
  school: number;
  school_name: string;
  is_active: boolean;
  teacher_profile: TeacherProfileSummary | null;
};

export type Student = {
  id: number;
  full_name: string;
  email: string;
  role: "student";
  school: number;
  school_name: string;
  is_active: boolean;
  student_profile: StudentProfileSummary | null;
};

export type TeacherProfile = {
  id: number;
  user: number;
  user_email: string;
  user_full_name: string;
  school: number;
  school_name: string;
  staff_id: string;
  phone_number: string;
};

export type StudentProfile = {
  id: number;
  user: number;
  user_email: string;
  user_full_name: string;
  school: number;
  school_name: string;
  admission_number: string;
  guardian_name: string;
  guardian_phone: string;
};

export type TeacherRegistrationPayload = {
  full_name: string;
  email: string;
  password: string;
  role: "teacher";
  school: number | null;
  staff_id: string;
  phone_number: string;
};

export type StudentRegistrationPayload = {
  full_name: string;
  email: string;
  password: string;
  role: "student";
  school: number | null;
  admission_number: string;
  guardian_name: string;
  guardian_phone: string;
};

export type RegisterUserPayload = TeacherRegistrationPayload | StudentRegistrationPayload;

export type TeacherProfilePayload = {
  user: number;
  school?: number;
  staff_id: string;
  phone_number?: string;
};

export type StudentProfilePayload = {
  user: number;
  school?: number;
  admission_number: string;
  guardian_name?: string;
  guardian_phone?: string;
};

export type UserListParams = {
  search?: string;
  school?: number | string;
  is_active?: boolean | string;
};

export type QueryParams = Record<
  string,
  string | number | boolean | null | undefined
>;

export type AssignmentStatus = "draft" | "published" | "closed" | "archived";

export type AssignmentQuestionPreview = {
  id: number;
  question_text: string;
  difficulty: "easy" | "medium" | "hard";
  source?: number | null;
  source_name?: string | null;
};

export type AssignmentQuestion = {
  id: number;
  assignment: number;
  question: number;
  question_detail?: AssignmentQuestionPreview;
  order: number;
  marks: number;
  created_at?: string;
  updated_at?: string;
};

export type Assignment = {
  id: number;
  school: number;
  school_name?: string;
  teacher: number;
  teacher_name?: string;
  class_arm: number;
  class_arm_name?: string;
  class_level_name?: string;
  subject: number;
  subject_name?: string;
  topic: number;
  topic_title?: string;
  lesson_log: number | null;
  lesson_log_display?: string | null;
  title: string;
  instructions: string;
  question_count: number;
  duration_minutes: number | null;
  starts_at: string | null;
  due_at: string | null;
  status: AssignmentStatus;
  status_display?: string;
  published_at: string | null;
  assignment_questions: AssignmentQuestion[];
  created_at: string;
  updated_at: string;
};

export type AssignmentGeneratePayload = {
  class_arm: number;
  subject: number;
  topic: number;
  lesson_log?: number | null;
  title: string;
  instructions?: string;
  question_count: number;
  duration_minutes?: number | null;
  starts_at?: string | null;
  due_at?: string | null;
};

export type LegacyRegisterUserPayload = {
  full_name: string;
  email: string;
  password: string;
  role: "teacher" | "student";
  school: number | null;
};
