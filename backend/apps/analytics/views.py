from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.analytics.permissions import (
    IsSchoolAdminAnalyticsUser,
    IsTeacherAnalyticsUser,
    IsTeacherOnlyAnalyticsUser,
)
from apps.analytics.serializers import (
    AdminInterventionDashboardSerializer,
    StudentProgressReportSerializer,
    TeacherRemediationPlanSerializer,
)
from apps.analytics.services import (
    get_admin_assignment_compliance,
    get_admin_class_performance,
    get_admin_intervention_dashboard,
    get_admin_overview,
    get_admin_subject_performance,
    get_admin_teacher_activity,
    get_admin_weak_students,
    get_assignment_results,
    get_student_performance_for_teacher,
    get_student_progress_report,
    get_teacher_remediation_plan,
    get_teacher_overview,
    get_teacher_weak_students,
    get_teacher_weak_topics,
)


def requested_school_id(request):
    return request.query_params.get("school")


class TeacherOverviewAPIView(APIView):
    permission_classes = [IsTeacherAnalyticsUser]

    def get(self, request):
        return Response(get_teacher_overview(request.user))


class TeacherAssignmentResultsAPIView(APIView):
    permission_classes = [IsTeacherAnalyticsUser]

    def get(self, request, assignment_id):
        return Response(get_assignment_results(request.user, assignment_id))


class TeacherWeakStudentsAPIView(APIView):
    permission_classes = [IsTeacherAnalyticsUser]

    def get(self, request):
        return Response(get_teacher_weak_students(request.user))


class TeacherWeakTopicsAPIView(APIView):
    permission_classes = [IsTeacherAnalyticsUser]

    def get(self, request):
        return Response(get_teacher_weak_topics(request.user))


class TeacherStudentPerformanceAPIView(APIView):
    permission_classes = [IsTeacherAnalyticsUser]

    def get(self, request, student_id):
        return Response(get_student_performance_for_teacher(request.user, student_id))


class TeacherRemediationPlanAPIView(APIView):
    permission_classes = [IsTeacherOnlyAnalyticsUser]

    def get(self, request):
        serializer = TeacherRemediationPlanSerializer(
            get_teacher_remediation_plan(request.user)
        )
        return Response(serializer.data)


class AdminOverviewAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        return Response(
            get_admin_overview(request.user, school_id=requested_school_id(request))
        )


class AdminClassPerformanceAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        return Response(
            get_admin_class_performance(
                request.user,
                school_id=requested_school_id(request),
            )
        )


class AdminSubjectPerformanceAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        return Response(
            get_admin_subject_performance(
                request.user,
                school_id=requested_school_id(request),
            )
        )


class AdminTeacherActivityAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        return Response(
            get_admin_teacher_activity(
                request.user,
                school_id=requested_school_id(request),
            )
        )


class AdminWeakStudentsAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        return Response(
            get_admin_weak_students(request.user, school_id=requested_school_id(request))
        )


class AdminAssignmentComplianceAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        return Response(
            get_admin_assignment_compliance(
                request.user,
                school_id=requested_school_id(request),
            )
        )


class AdminInterventionDashboardAPIView(APIView):
    permission_classes = [IsSchoolAdminAnalyticsUser]

    def get(self, request):
        serializer = AdminInterventionDashboardSerializer(
            get_admin_intervention_dashboard(
                request.user,
                school_id=requested_school_id(request),
            )
        )
        return Response(serializer.data)


class StudentProgressReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        serializer = StudentProgressReportSerializer(
            get_student_progress_report(
                request.user,
                student_id,
                school_id=requested_school_id(request),
            )
        )
        return Response(serializer.data)
