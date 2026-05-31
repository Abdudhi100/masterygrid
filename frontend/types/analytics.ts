export type AdminRecentAssignment = {
  id: number;
  title: string;
  teacher_name: string;
  class_arm: string;
  subject: string;
  topic: string;
  status: string;
  due_at: string | null;
  created_at: string;
};

export type AdminRecentLowPerformingStudent = {
  student_id: number;
  student_name: string;
  admission_number: string | null;
  class_arm: string | null;
  assignment_id: number;
  assignment_title: string;
  percentage: number;
  graded_at: string | null;
};

export type AdminOverview = {
  total_students: number;
  total_teachers: number;
  total_class_arms: number;
  total_subjects: number;
  total_assignments: number;
  published_assignments: number;
  draft_assignments: number;
  closed_assignments: number;
  total_submissions: number;
  graded_submissions: number;
  pending_or_not_started_submissions: number;
  average_school_percentage: number;
  weak_students_count: number;
  weak_classes_count: number;
  weak_subjects_count: number;
  recent_assignments: AdminRecentAssignment[];
  recent_low_performing_students: AdminRecentLowPerformingStudent[];
};

export type AdminClassPerformance = {
  class_arm_id: number;
  class_level: string;
  class_arm_name: string;
  total_students: number;
  total_assignments: number;
  total_submissions: number;
  average_percentage: number;
  submission_rate: number;
  weak_student_count: number;
  risk_level: string;
  recommendation: string;
};

export type AdminWeakestTopic = {
  topic: string;
  average_percentage: number;
  total_submissions: number;
};

export type AdminSubjectPerformance = {
  subject_id: number;
  subject_name: string;
  total_assignments: number;
  total_submissions: number;
  average_percentage: number;
  weak_topic_count: number;
  weakest_topics: AdminWeakestTopic[];
  risk_level: string;
  recommendation: string;
};

export type AdminTeacherActivity = {
  teacher_id: number;
  teacher_name: string;
  staff_id: string | null;
  assigned_classes_count: number;
  assigned_subjects_count: number;
  assignments_created: number;
  published_assignments: number;
  total_student_submissions: number;
  average_class_performance: number;
  last_assignment_date: string | null;
  activity_status: string;
  recommendation: string;
};

export type AdminWeakSubject = {
  subject: string;
  average_percentage: number;
  submission_count: number;
};

export type AdminWeakStudent = {
  student_id: number;
  student_name: string;
  admission_number: string | null;
  class_arm: string | null;
  average_percentage: number;
  graded_submission_count: number;
  missed_assignment_count: number;
  weak_subjects: AdminWeakSubject[];
  weak_topics: StudentWeakTopic[];
  risk_level: string;
  recommendation: string;
};

export type AdminAssignmentCompliance = {
  assignment_id: number;
  title: string;
  teacher_name: string;
  class_arm: string;
  subject: string;
  topic: string;
  status: string;
  due_at: string | null;
  expected_students: number;
  started_count: number;
  submitted_count: number;
  graded_count: number;
  not_started_count: number;
  submission_rate: number;
  compliance_status: string;
};

export type TeacherRecentAssignment = {
  id: number;
  title: string;
  subject: string;
  topic: string;
  class_arm: string;
  status: string;
  due_at: string | null;
  question_count: number;
  created_at: string;
  submission_count: number;
};

export type TeacherRecentLowPerformingStudent = {
  student_id: number;
  student_name: string;
  assignment_id: number;
  assignment_title: string;
  topic: string;
  percentage: number;
  graded_at: string | null;
};

export type TeacherWeakTopic = {
  subject: string;
  topic: string;
  class_arm: string;
  average_percentage: number;
  total_submissions: number;
  weak_student_count: number;
  recommendation: string;
};

export type RemediationAffectedStudent = {
  student_id: number;
  student_name: string;
  admission_number: string | null;
  class_arm: string;
  topic_id: number;
  topic_title: string;
  average_score: number;
  attempted_count: number;
};

export type RemediationActionPayload = {
  class_arm: number;
  subject: number;
  topic: number;
  question_count: number;
  title: string;
  instructions: string;
  remedial: boolean;
};

export type RemediationTopicCard = {
  subject_id: number;
  subject: string;
  topic_id: number;
  topic: string;
  class_arm_id: number;
  class_arm: string;
  class_level_id: number;
  class_level: string;
  average_score: number;
  attempted_count: number;
  weak_student_count: number;
  available_approved_questions: number;
  recommended_question_count: number;
  suggested_assignment_title: string;
  suggested_instructions: string;
  recommended_action: string;
  priority: "high" | "medium" | "low";
  latest_assignment_id: number;
  latest_assignment_title: string;
  latest_assignment_created_at: string;
  affected_students: RemediationAffectedStudent[];
  action_payload: RemediationActionPayload;
};

export type TeacherRemediationPlan = {
  summary: {
    total_weak_topics: number;
    actionable_topic_count: number;
    total_affected_students: number;
    total_graded_submissions: number;
    average_score: number;
    message: string;
  };
  recommended_actions: RemediationTopicCard[];
  weak_topic_cards: RemediationTopicCard[];
  affected_students: RemediationAffectedStudent[];
};

export type TeacherOverview = {
  total_assignments_created: number;
  published_assignments: number;
  draft_assignments: number;
  closed_assignments: number;
  total_submissions: number;
  graded_submissions: number;
  pending_submissions: number;
  average_score_percentage: number;
  recent_assignments: TeacherRecentAssignment[];
  recent_low_performing_students: TeacherRecentLowPerformingStudent[];
  weak_topics_summary: TeacherWeakTopic[];
};

export type StudentWeakTopic = {
  subject?: string;
  topic: string;
  average_percentage: number;
  submission_count?: number;
  graded_submission_count?: number;
};

export type TeacherWeakStudent = {
  student_id: number;
  student_name: string;
  class_arm: string | null;
  average_percentage: number;
  graded_submission_count: number;
  missed_assignment_count: number;
  weak_topics: StudentWeakTopic[];
  risk_level: string;
  recommendation: string;
};

export type StudentPerformanceGroup = {
  subject?: string;
  topic?: string;
  average_percentage: number;
  graded_submission_count: number;
};

export type StudentRecentScore = {
  assignment_id: number;
  assignment_title: string;
  subject: string;
  topic: string;
  score: number;
  total_marks: number;
  percentage: number;
  graded_at: string | null;
};

export type StudentMissedAssignment = {
  assignment_id: number;
  title: string;
  subject: string;
  topic: string;
  due_at: string | null;
};

export type TeacherStudentPerformance = {
  student: {
    id: number;
    name: string;
    email: string;
    admission_number: string | null;
    class_arm: string | null;
  };
  average_percentage: number;
  assignments_attempted: number;
  missed_assignments: StudentMissedAssignment[];
  performance_by_subject: StudentPerformanceGroup[];
  performance_by_topic: StudentPerformanceGroup[];
  recent_scores: StudentRecentScore[];
  weak_topics: StudentWeakTopic[];
  recommendation: string;
};

export type AssignmentResultSummary = {
  total_students_expected: number;
  total_started: number;
  total_submitted: number;
  total_graded: number;
  total_not_started: number;
  submission_rate: number;
  average_percentage: number;
  highest_percentage: number;
  lowest_percentage: number;
};

export type StudentResultRow = {
  student_id: number;
  student_name: string;
  admission_number: string | null;
  status: string;
  score: number;
  total_marks: number;
  percentage: number;
  submitted_at: string | null;
  time_spent_seconds: number | null;
};

export type QuestionPerformanceRow = {
  assignment_question_id: number;
  question_text: string;
  total_attempts: number;
  correct_count: number;
  wrong_count: number;
  correct_percentage: number;
};

export type MostMissedQuestion = {
  question_text: string;
  wrong_count: number;
  correct_percentage: number;
};

export type TeacherAssignmentResults = {
  assignment: {
    id: number;
    title: string;
    subject: string;
    topic: string;
    class_arm: string;
    status: string;
    question_count: number;
    due_at: string | null;
  };
  submission_summary: AssignmentResultSummary;
  student_results: StudentResultRow[];
  question_performance: QuestionPerformanceRow[];
  most_missed_questions: MostMissedQuestion[];
};

export type StudentAssignment = {
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
  submission_status: string | null;
};
