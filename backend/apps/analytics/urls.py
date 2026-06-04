from django.urls import path

from apps.analytics.views import (
    AdminAssignmentComplianceAPIView,
    AdminClassPerformanceAPIView,
    AdminInterventionDashboardAPIView,
    AdminOverviewAPIView,
    AdminSubjectPerformanceAPIView,
    AdminTeacherActivityAPIView,
    AdminWeakStudentsAPIView,
    StudentDashboardAPIView,
    StudentProgressReportAPIView,
    TeacherAssignmentResultsAPIView,
    TeacherOverviewAPIView,
    TeacherRemediationPlanAPIView,
    TeacherStudentPerformanceAPIView,
    TeacherWeakStudentsAPIView,
    TeacherWeakTopicsAPIView,
)

app_name = "analytics"

urlpatterns = [
    path("admin/overview/", AdminOverviewAPIView.as_view(), name="admin-overview"),
    path(
        "admin/class-performance/",
        AdminClassPerformanceAPIView.as_view(),
        name="admin-class-performance",
    ),
    path(
        "admin/subject-performance/",
        AdminSubjectPerformanceAPIView.as_view(),
        name="admin-subject-performance",
    ),
    path(
        "admin/teacher-activity/",
        AdminTeacherActivityAPIView.as_view(),
        name="admin-teacher-activity",
    ),
    path(
        "admin/weak-students/",
        AdminWeakStudentsAPIView.as_view(),
        name="admin-weak-students",
    ),
    path(
        "admin/assignment-compliance/",
        AdminAssignmentComplianceAPIView.as_view(),
        name="admin-assignment-compliance",
    ),
    path(
        "admin/intervention-dashboard/",
        AdminInterventionDashboardAPIView.as_view(),
        name="admin-intervention-dashboard",
    ),
    path("teacher/overview/", TeacherOverviewAPIView.as_view(), name="teacher-overview"),
    path(
        "students/<int:student_id>/progress-report/",
        StudentProgressReportAPIView.as_view(),
        name="student-progress-report",
    ),
    path(
        "student/dashboard/",
        StudentDashboardAPIView.as_view(),
        name="student-dashboard",
    ),
    path(
        "teacher/assignments/<int:assignment_id>/results/",
        TeacherAssignmentResultsAPIView.as_view(),
        name="teacher-assignment-results",
    ),
    path(
        "teacher/weak-students/",
        TeacherWeakStudentsAPIView.as_view(),
        name="teacher-weak-students",
    ),
    path(
        "teacher/weak-topics/",
        TeacherWeakTopicsAPIView.as_view(),
        name="teacher-weak-topics",
    ),
    path(
        "teacher/remediation-plan/",
        TeacherRemediationPlanAPIView.as_view(),
        name="teacher-remediation-plan",
    ),
    path(
        "teacher/students/<int:student_id>/performance/",
        TeacherStudentPerformanceAPIView.as_view(),
        name="teacher-student-performance",
    ),
]
