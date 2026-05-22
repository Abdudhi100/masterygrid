import type { NavItem } from "@/types/common";
import type { UserRole } from "@/types/auth";

export const adminNavItems: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard" },
  { label: "Academic Sessions", href: "/admin/academic-sessions" },
  { label: "Terms", href: "/admin/terms" },
  { label: "Class Levels", href: "/admin/class-levels" },
  { label: "Class Arms", href: "/admin/class-arms" },
  { label: "Subjects", href: "/admin/subjects" },
  { label: "Topics", href: "/admin/topics" },
  { label: "Teachers", href: "/admin/teachers" },
  { label: "Students", href: "/admin/students" },
  { label: "Teacher Assignments", href: "/admin/teacher-assignments" },
  { label: "Student Enrollments", href: "/admin/student-enrollments" },
  { label: "Question Bank", href: "/admin/question-bank" },
  { label: "Question Sources", href: "/admin/question-bank/sources" },
  { label: "Analytics", href: "/admin/analytics" },
  { label: "Class Performance", href: "/admin/analytics/classes" },
  { label: "Subject Performance", href: "/admin/analytics/subjects" },
  { label: "Teacher Activity", href: "/admin/analytics/teachers" },
  { label: "Weak Students", href: "/admin/analytics/weak-students" },
  { label: "Assignment Compliance", href: "/admin/analytics/compliance" }
];

export const teacherNavItems: NavItem[] = [
  { label: "Dashboard", href: "/teacher/dashboard" },
  { label: "Lessons", href: "/teacher/lessons" },
  { label: "Assignments", href: "/teacher/assignments" },
  { label: "Results", href: "/teacher/results" },
  { label: "Weak Students", href: "/teacher/weak-students" },
  { label: "Weak Topics", href: "/teacher/weak-topics" },
  { label: "Question Bank", href: "/teacher/question-bank" }
];

export const studentNavItems: NavItem[] = [
  { label: "Dashboard", href: "/student/dashboard" },
  { label: "My Assignments", href: "/student/assignments" }
];

export function dashboardPathForRole(role: UserRole): string {
  if (role === "teacher") {
    return "/teacher/dashboard";
  }

  if (role === "student") {
    return "/student/dashboard";
  }

  return "/admin/dashboard";
}
