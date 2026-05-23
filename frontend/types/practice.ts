import type { QuestionMedia } from "@/types/questionBank";

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
  media?: QuestionMedia[];
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
  media?: QuestionMedia[];
};

export type PracticeResult = PracticeSession & {
  answers: PracticeResultAnswer[];
};

export type PracticeSummary = {
  total_sessions_completed: number;
  total_questions_answered: number;
  total_correct_answers: number;
  overall_average_percentage: number | null;
  best_percentage: number | null;
  lowest_percentage: number | null;
  last_practice_at: string | null;
  best_subject: string | null;
  weakest_subject: string | null;
};

export type PracticeSubjectPerformance = {
  subject_id: number;
  subject_name: string;
  sessions_completed: number;
  questions_answered: number;
  correct_answers: number;
  average_percentage: number | null;
  last_practiced_at: string | null;
};

export type PracticeTopicStrength = "strong" | "average" | "weak";

export type PracticeTopicPerformance = {
  topic_id: number;
  topic_title: string;
  subject_id: number;
  subject_name: string;
  sessions_completed: number;
  questions_answered: number;
  correct_answers: number;
  average_percentage: number | null;
  last_practiced_at: string | null;
  strength_level: PracticeTopicStrength;
};

export type PracticeRecommendationPriority = "high" | "medium" | "low";

export type PracticeRecommendation = {
  subject_id: number;
  subject_name: string;
  topic_id: number;
  topic_title: string;
  priority: PracticeRecommendationPriority;
  reason: string;
  recommended_difficulty: PracticeDifficulty;
  available_question_count: number;
  suggested_question_count: number;
};

export type PracticeRecentSession = {
  id: number;
  subject_id: number;
  subject_name: string;
  topic_id: number | null;
  topic_title: string | null;
  difficulty: PracticeDifficulty;
  question_count_requested: number;
  score: number;
  total_marks: number;
  percentage: number | null;
  started_at: string;
  submitted_at: string | null;
};

export type PracticeAnalyticsDashboard = {
  summary: PracticeSummary;
  subject_performance: PracticeSubjectPerformance[];
  topic_performance: PracticeTopicPerformance[];
  weak_topics: PracticeTopicPerformance[];
  strong_topics: PracticeTopicPerformance[];
  recommendations: PracticeRecommendation[];
  recent_sessions: PracticeRecentSession[];
  message: string;
};
