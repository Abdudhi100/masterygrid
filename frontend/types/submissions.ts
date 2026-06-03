import type { QuestionMedia } from "@/types/questionBank";
import type { AssignmentDeadlineStatus } from "@/types/academics";

export type SubmissionStatus =
  | "not_started"
  | "in_progress"
  | "submitted"
  | "graded"
  | "auto_submitted";

export type StudentAssignmentItem = {
  id: number;
  title: string;
  instructions: string;
  subject_name: string;
  topic_title: string;
  class_arm_name: string;
  question_count: number;
  duration_minutes: number | null;
  starts_at: string | null;
  due_at: string | null;
  original_due_at: string | null;
  allow_late_submissions: boolean;
  late_submission_deadline: string | null;
  deadline_extended_at: string | null;
  deadline_status: AssignmentDeadlineStatus;
  is_overdue: boolean;
  is_due_soon: boolean;
  can_submit_now: boolean;
  status: string;
  submission_id: number | null;
  submission_status: SubmissionStatus | null;
  is_late: boolean;
  submitted_after_due_seconds: number | null;
};

export type SubmissionQuestionOption = {
  id: number;
  label: string;
  text: string;
};

export type SubmissionQuestion = {
  assignment_question: number;
  question: number;
  question_text: string;
  marks: number;
  options: SubmissionQuestionOption[];
  media?: QuestionMedia[];
};

export type Submission = {
  id: number;
  school: number;
  assignment: number;
  assignment_title: string;
  student: number;
  student_name: string;
  subject_name: string;
  topic_title: string;
  class_arm_name: string;
  status: SubmissionStatus;
  started_at: string | null;
  submitted_at: string | null;
  graded_at: string | null;
  score: number;
  total_marks: number;
  percentage: string | number;
  time_spent_seconds: number | null;
  is_late: boolean;
  submitted_after_due_seconds: number | null;
  deadline_status_at_submit: AssignmentDeadlineStatus | "";
  deadline_status: AssignmentDeadlineStatus;
  assignment_due_at: string | null;
  assignment_original_due_at: string | null;
  assignment_allow_late_submissions: boolean;
  assignment_late_submission_deadline: string | null;
  created_at: string;
  updated_at: string;
};

export type SubmissionStart = Submission & {
  questions: SubmissionQuestion[];
};

export type StudentAnswerInput = {
  assignment_question: number;
  selected_option: number;
};

export type SubmissionResultOption = {
  id: number;
  label: string;
  text: string;
};

export type SubmissionResultAnswer = {
  assignment_question: number;
  question_text: string;
  selected_option: SubmissionResultOption | null;
  correct_option: SubmissionResultOption | null;
  is_correct: boolean;
  marks_awarded: number;
  explanation: string;
  media?: QuestionMedia[];
};

export type SubmissionResult = Submission & {
  answers: SubmissionResultAnswer[];
};
