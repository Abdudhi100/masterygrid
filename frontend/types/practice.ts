export type PracticeDifficulty = "easy" | "medium" | "hard" | "mixed";

export type PracticeStatus = "in_progress" | "submitted" | "abandoned";

export type PracticeOption = {
  id: number;
  label: string;
  text: string;
};

export type PracticeSessionQuestion = {
  session_question: number;
  order: number;
  question_text: string;
  marks: number;
  options: PracticeOption[];
};

export type PracticeSession = {
  id: number;
  school: number;
  student: number;
  subject: number;
  subject_name: string;
  topic: number | null;
  topic_title: string | null;
  class_level: number | null;
  class_level_name: string | null;
  class_arm: number | null;
  class_arm_name: string | null;
  difficulty: PracticeDifficulty;
  question_count_requested: number;
  status: PracticeStatus;
  score: number;
  total_marks: number;
  percentage: string | number | null;
  started_at: string;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
  questions?: PracticeSessionQuestion[];
};

export type PracticeStartPayload = {
  subject: number;
  topic?: number | null;
  class_level?: number | null;
  difficulty: PracticeDifficulty;
  question_count: number;
};

export type PracticeAnswerInput = {
  session_question: number;
  selected_option: number;
};

export type PracticeSubmitPayload = {
  answers: PracticeAnswerInput[];
};

export type PracticeResultOption = {
  id: number | null;
  label: string;
  text: string;
};

export type PracticeResultAnswer = {
  session_question: number;
  question_text: string;
  selected_option: PracticeResultOption | null;
  correct_option: PracticeResultOption | null;
  is_correct: boolean;
  marks_awarded: number;
  explanation: string;
};

export type PracticeResult = PracticeSession & {
  answers: PracticeResultAnswer[];
};
