import type { AssignmentDeadlineStatus } from "@/types/academics";
import type {
  LearningPathStatus,
  LearningPathTopicCard,
  PracticeRecentSession,
  PracticeTopicPerformance
} from "@/types/practice";
import type {
  NotificationPriority,
  NotificationStatus,
  NotificationType
} from "@/types/notifications";

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
  deadline_status: string;
  expected_students: number;
  started_count: number;
  submitted_count: number;
  graded_count: number;
  late_submission_count: number;
  not_started_count: number;
  submission_rate: number;
  compliance_status: string;
};

export type InterventionRiskLevel = "critical" | "high" | "moderate" | "low";

export type AdminInterventionActionPayload = {
  label: string;
  href: string;
  params: Record<string, string | number | boolean>;
};

export type AdminInterventionSummary = {
  total_classes_at_risk: number;
  total_subjects_at_risk: number;
  total_teachers_at_risk: number;
  total_weak_student_clusters: number;
  total_compliance_alerts: number;
  total_urgent_interventions: number;
  average_school_percentage: number;
  overall_risk_level: InterventionRiskLevel;
  message: string;
};

export type AdminUrgentIntervention = {
  category: string;
  title: string;
  description: string;
  risk_level: InterventionRiskLevel;
  recommended_action: string;
  action_payload: AdminInterventionActionPayload;
};

export type AdminClassIntervention = {
  class_arm_id: number;
  class_arm_name: string;
  class_level: string;
  average_score: number;
  submitted_count: number;
  weak_student_count: number;
  risk_level: InterventionRiskLevel;
  main_weak_subjects: Array<{
    subject: string;
    average_percentage: number;
    weak_student_count: number;
  }>;
  main_weak_topics: Array<{
    subject: string;
    topic: string;
    average_percentage: number;
    weak_student_count: number;
  }>;
  recommended_action: string;
  action_payload: AdminInterventionActionPayload;
};

export type AdminSubjectIntervention = {
  subject_id: number;
  subject_name: string;
  average_score: number;
  weak_class_count: number;
  weak_student_count: number;
  affected_class_arms: string[];
  risk_level: InterventionRiskLevel;
  weakest_topics: AdminWeakestTopic[];
  recommended_action: string;
  action_payload: AdminInterventionActionPayload;
};

export type AdminTeacherIntervention = {
  teacher_id: number;
  teacher_name: string;
  teacher_email: string;
  staff_id: string | null;
  classes_subjects_taught: Array<{
    class_arm_id: number;
    class_arm_name: string;
    subject_id: number;
    subject_name: string;
  }>;
  assignment_count: number;
  published_assignment_count: number;
  average_class_score: number;
  submission_rate: number;
  submitted_count: number;
  expected_submission_count: number;
  risk_level: InterventionRiskLevel;
  recommended_action: string;
  action_payload: AdminInterventionActionPayload;
};

export type AdminWeakStudentCluster = {
  class_arm: string;
  subject: string;
  topic: string;
  weak_student_count: number;
  average_score: number;
  risk_level: InterventionRiskLevel;
  recommended_action: string;
  action_payload: AdminInterventionActionPayload;
};

export type AdminAssignmentComplianceAlert = {
  assignment_id: number;
  title: string;
  teacher_name: string;
  class_arm: string;
  subject: string;
  topic: string;
  expected_students: number;
  started_count: number;
  submitted_count: number;
  not_started_count: number;
  submission_rate: number;
  risk_level: InterventionRiskLevel;
  recommended_action: string;
  action_payload: AdminInterventionActionPayload;
};

export type AdminInterventionDashboard = {
  summary: AdminInterventionSummary;
  risk_score: number;
  overall_risk_level: InterventionRiskLevel;
  urgent_interventions: AdminUrgentIntervention[];
  class_interventions: AdminClassIntervention[];
  subject_interventions: AdminSubjectIntervention[];
  teacher_interventions: AdminTeacherIntervention[];
  weak_student_clusters: AdminWeakStudentCluster[];
  assignment_compliance_alerts: AdminAssignmentComplianceAlert[];
  recommended_actions: AdminUrgentIntervention[];
};

export type StudentDashboardSummary = {
  pending_assignments_count: number;
  overdue_assignments_count: number;
  due_soon_assignments_count: number;
  graded_assignments_count: number;
  assignment_average: number;
  practice_sessions_count: number;
  practice_average: number;
  unread_notifications_count: number;
};

export type StudentDashboardAssignment = {
  id: number;
  title: string;
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
  deadline_status: AssignmentDeadlineStatus;
  is_overdue: boolean;
  is_due_soon: boolean;
  can_submit_now: boolean;
  submission_id: number | null;
  submission_status: string | null;
  is_late: boolean;
  submitted_after_due_seconds: number | null;
  href: string;
};

export type StudentDashboardRecentResult = {
  submission_id: number;
  assignment_id: number;
  assignment_title: string;
  subject_name: string;
  topic_title: string;
  score: number;
  total_marks: number;
  percentage: number;
  submitted_at: string | null;
  graded_at: string | null;
  is_late: boolean;
  href: string;
};

export type StudentDashboardNotification = {
  id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  status: NotificationStatus;
  target_url: string;
  created_at: string;
};

export type StudentDashboardQuickAction = {
  title: string;
  href: string;
  priority: "urgent" | "high" | "medium" | "low" | "normal" | string;
};

export type StudentDashboard = {
  summary: StudentDashboardSummary;
  assignments: {
    pending: StudentDashboardAssignment[];
    due_soon: StudentDashboardAssignment[];
    overdue: StudentDashboardAssignment[];
    recently_graded: StudentDashboardRecentResult[];
  };
  practice: {
    recent_sessions: PracticeRecentSession[];
    average: number;
    weak_topics: PracticeTopicPerformance[];
    strong_topics: PracticeTopicPerformance[];
  };
  learning_path: {
    overall_status: LearningPathStatus;
    headline: string;
    message: string;
    recommended_next_action: LearningPathTopicCard | null;
    top_topic_card: LearningPathTopicCard | null;
  };
  notifications: StudentDashboardNotification[];
  quick_actions: StudentDashboardQuickAction[];
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

export type TeacherDashboardSummary = {
  active_assignments_count: number;
  draft_assignments_count: number;
  published_assignments_count: number;
  overdue_assignments_count: number;
  low_submission_assignments_count: number;
  weak_students_count: number;
  weak_topics_count: number;
  open_interventions_count: number;
  unread_notifications_count: number;
};

export type TeacherDashboardAssignment = {
  id: number;
  title: string;
  subject: string;
  topic: string;
  class_arm: string;
  status: string;
  deadline_status: AssignmentDeadlineStatus;
  due_at: string | null;
  question_count: number;
  created_at: string;
  expected_students: number;
  submitted_count: number;
  graded_count: number;
  late_submission_count: number;
  submission_rate: number;
  href: string;
  results_href: string;
};

export type TeacherDashboardRecentSubmission = {
  id: number;
  assignment_id: number;
  assignment_title: string;
  student_id: number;
  student_name: string;
  subject: string;
  topic: string;
  status: string;
  score: number;
  total_marks: number;
  percentage: number;
  submitted_at: string | null;
  graded_at: string | null;
  is_late: boolean;
  results_href: string;
};

export type TeacherDashboardIntervention = {
  id: number;
  title: string;
  student_id: number;
  student_name: string;
  category: string;
  priority: string;
  status: string;
  due_date: string | null;
  updated_at: string;
  href: string;
};

export type TeacherDashboardNotification = {
  id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  status: NotificationStatus;
  target_url: string;
  created_at: string;
};

export type TeacherDashboardQuickAction = {
  title: string;
  href: string;
  priority: "urgent" | "high" | "medium" | "low" | "normal" | string;
};

export type TeacherDashboard = {
  summary: TeacherDashboardSummary;
  assignments: {
    recent_assignments: TeacherDashboardAssignment[];
    overdue_assignments: TeacherDashboardAssignment[];
    low_submission_assignments: TeacherDashboardAssignment[];
  };
  submissions: {
    recent_submissions: TeacherDashboardRecentSubmission[];
  };
  weak_students: TeacherWeakStudent[];
  weak_topics: TeacherWeakTopic[];
  remediation: {
    recommended_actions: RemediationTopicCard[];
    summary: TeacherRemediationPlan["summary"];
  };
  interventions: TeacherDashboardIntervention[];
  notifications: TeacherDashboardNotification[];
  quick_actions: TeacherDashboardQuickAction[];
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

export type StudentProgressRiskLevel = "critical" | "high" | "moderate" | "low";

export type StudentProgressProfile = {
  id: number;
  full_name: string;
  email: string;
  admission_number: string | null;
  class_arm: string | null;
  class_arm_id: number | null;
  class_level: string | null;
  class_level_id: number | null;
  school: string | null;
  school_id: number | null;
};

export type StudentProgressSummary = {
  assignment_average: number;
  practice_average: number;
  overall_average: number;
  graded_assignments_count: number;
  missed_assignments_count: number;
  practice_sessions_count: number;
  weak_topic_count: number;
  strong_topic_count: number;
  risk_level: StudentProgressRiskLevel;
};

export type StudentProgressAssignmentResult = {
  submission_id: number;
  assignment_id: number;
  assignment_title: string;
  teacher_name: string;
  class_arm: string;
  subject_id: number;
  subject_name: string;
  topic_id: number;
  topic_title: string;
  score: number;
  total_marks: number;
  percentage: number;
  submitted_at: string | null;
  graded_at: string | null;
};

export type StudentProgressSubjectBreakdown = {
  subject_id: number;
  subject_name: string;
  average_percentage: number;
  graded_assignments_count?: number;
  sessions_completed?: number;
  questions_answered?: number;
  correct_answers?: number;
  last_graded_at?: string | null;
  last_practiced_at?: string | null;
};

export type StudentProgressTopicBreakdown = StudentProgressSubjectBreakdown & {
  topic_id: number;
  topic_title: string;
};

export type StudentProgressMissedAssignment = {
  assignment_id: number;
  title: string;
  subject: string;
  topic: string;
  due_at: string | null;
};

export type StudentProgressPracticeSession = {
  id: number;
  subject_id: number;
  subject_name: string;
  topic_id: number | null;
  topic_title: string | null;
  class_level_id: number | null;
  class_level_name: string | null;
  difficulty: string;
  question_count_requested: number;
  score: number;
  total_marks: number;
  percentage: number;
  submitted_at: string | null;
};

export type StudentProgressTopic = {
  subject_id: number;
  subject_name: string;
  topic_id: number;
  topic_title: string;
  assignment_average: number | null;
  practice_average: number | null;
  assignment_count: number;
  practice_sessions_count: number;
  average_percentage: number;
  evidence_count: number;
};

export type StudentProgressRecommendation = {
  recommended_action: string;
  subject_id: number | null;
  subject_name: string;
  topic_id: number | null;
  topic_title: string;
  reason: string;
  action_payload: Record<string, string | number | boolean | null>;
};

export type StudentProgressReport = {
  student: StudentProgressProfile;
  summary: StudentProgressSummary;
  assignment_performance: {
    recent_results: StudentProgressAssignmentResult[];
    subject_breakdown: StudentProgressSubjectBreakdown[];
    topic_breakdown: StudentProgressTopicBreakdown[];
    missed_assignments: StudentProgressMissedAssignment[];
  };
  practice_performance: {
    recent_sessions: StudentProgressPracticeSession[];
    subject_breakdown: StudentProgressSubjectBreakdown[];
    topic_breakdown: StudentProgressTopicBreakdown[];
  };
  weak_topics: StudentProgressTopic[];
  strong_topics: StudentProgressTopic[];
  recommendations: StudentProgressRecommendation[];
  learning_path_summary: {
    overall_status: string;
    headline: string;
    message: string;
    recommended_next_action: Record<string, unknown> | null;
  };
  generated_at: string;
};

export type AssignmentResultSummary = {
  total_students_expected: number;
  total_started: number;
  total_submitted: number;
  total_graded: number;
  total_late: number;
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
  is_late: boolean;
  submitted_after_due_seconds: number | null;
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
    original_due_at: string | null;
    allow_late_submissions: boolean;
    late_submission_deadline: string | null;
    deadline_status: string;
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
