import { api } from "@/lib/api";
import type {
  AdminAssignmentCompliance,
  AdminClassPerformance,
  AdminInterventionDashboard,
  AdminOverview,
  AdminSubjectPerformance,
  AdminTeacherActivity,
  AdminWeakStudent,
  StudentDashboard,
  TeacherAssignmentResults,
  TeacherOverview,
  TeacherRemediationPlan,
  StudentProgressReport,
  TeacherStudentPerformance,
  TeacherWeakStudent,
  TeacherWeakTopic
} from "@/types/analytics";

export const getAdminOverview = () =>
  api.get<AdminOverview>("/analytics/admin/overview/");

export const getAdminClassPerformance = () =>
  api.get<AdminClassPerformance[]>("/analytics/admin/class-performance/");

export const getAdminSubjectPerformance = () =>
  api.get<AdminSubjectPerformance[]>("/analytics/admin/subject-performance/");

export const getAdminTeacherActivity = () =>
  api.get<AdminTeacherActivity[]>("/analytics/admin/teacher-activity/");

export const getAdminWeakStudents = () =>
  api.get<AdminWeakStudent[]>("/analytics/admin/weak-students/");

export const getAdminAssignmentCompliance = () =>
  api.get<AdminAssignmentCompliance[]>(
    "/analytics/admin/assignment-compliance/"
  );

export const getAdminInterventionDashboard = () =>
  api.get<AdminInterventionDashboard>(
    "/analytics/admin/intervention-dashboard/"
  );

export const getStudentDashboard = () =>
  api.get<StudentDashboard>("/analytics/student/dashboard/");

export const getTeacherOverview = () =>
  api.get<TeacherOverview>("/analytics/teacher/overview/");

export const getTeacherAssignmentResults = (assignmentId: number | string) =>
  api.get<TeacherAssignmentResults>(
    `/analytics/teacher/assignments/${assignmentId}/results/`
  );

export const getTeacherWeakStudents = () =>
  api.get<TeacherWeakStudent[]>("/analytics/teacher/weak-students/");

export const getTeacherWeakTopics = () =>
  api.get<TeacherWeakTopic[]>("/analytics/teacher/weak-topics/");

export const getTeacherRemediationPlan = () =>
  api.get<TeacherRemediationPlan>("/analytics/teacher/remediation-plan/");

export const getTeacherStudentPerformance = (studentId: number | string) =>
  api.get<TeacherStudentPerformance>(
    `/analytics/teacher/students/${studentId}/performance/`
  );

export const getStudentProgressReport = (studentId: number | string) =>
  api.get<StudentProgressReport>(
    `/analytics/students/${studentId}/progress-report/`
  );
