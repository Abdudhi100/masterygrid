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
  status: string;
  submission_id: number | null;
  submission_status: SubmissionStatus | null;
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
};

export type SubmissionResult = Submission & {
  answers: SubmissionResultAnswer[];
};
