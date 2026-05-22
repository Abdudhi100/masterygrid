from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
from apps.academics.permissions import AcademicRolePermission
from apps.academics.selectors import filter_queryset_for_user, is_platform_admin
from apps.academics.serializers import (
    AcademicSessionSerializer,
    ClassArmSerializer,
    ClassLevelSerializer,
    LessonLogSerializer,
    StudentEnrollmentSerializer,
    SubjectSerializer,
    TeacherClassSubjectAssignmentSerializer,
    TermSerializer,
    TopicSerializer,
)
from apps.common.choices import UserRole


class AcademicBaseViewSet(viewsets.ModelViewSet):
    permission_classes = [AcademicRolePermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        return filter_queryset_for_user(queryset, self.request.user)

    def get_save_kwargs(self):
        user = self.request.user
        if is_platform_admin(user):
            return {}

        save_kwargs = {}
        if hasattr(self.model, "school"):
            save_kwargs["school"] = user.school

        if self.model is LessonLog and user.role == UserRole.TEACHER:
            save_kwargs["teacher"] = user

        return save_kwargs

    def perform_create(self, serializer):
        serializer.save(**self.get_save_kwargs())

    def perform_update(self, serializer):
        serializer.save(**self.get_save_kwargs())


class AcademicSessionViewSet(AcademicBaseViewSet):
    model = AcademicSession
    serializer_class = AcademicSessionSerializer
    queryset = AcademicSession.objects.select_related("school").all()
    filterset_fields = ["school", "is_active", "name"]
    search_fields = ["name", "school__name"]
    ordering_fields = ["name", "starts_at", "ends_at", "created_at"]


class TermViewSet(AcademicBaseViewSet):
    model = Term
    serializer_class = TermSerializer
    queryset = Term.objects.select_related("school", "academic_session").all()
    filterset_fields = ["school", "academic_session", "name", "is_active"]
    search_fields = ["name", "school__name", "academic_session__name"]
    ordering_fields = ["starts_at", "ends_at", "created_at"]


class ClassLevelViewSet(AcademicBaseViewSet):
    model = ClassLevel
    serializer_class = ClassLevelSerializer
    queryset = ClassLevel.objects.select_related("school").all()
    filterset_fields = ["school", "name", "is_active"]
    search_fields = ["name", "description", "school__name"]
    ordering_fields = ["name", "created_at"]


class ClassArmViewSet(AcademicBaseViewSet):
    model = ClassArm
    serializer_class = ClassArmSerializer
    queryset = ClassArm.objects.select_related("school", "class_level").all()
    filterset_fields = ["school", "class_level", "name", "is_active"]
    search_fields = ["name", "description", "class_level__name", "school__name"]
    ordering_fields = ["name", "created_at"]


class SubjectViewSet(AcademicBaseViewSet):
    model = Subject
    serializer_class = SubjectSerializer
    queryset = Subject.objects.select_related("school").all()
    filterset_fields = ["school", "is_jamb_subject", "is_active"]
    search_fields = ["name", "code", "description", "school__name"]
    ordering_fields = ["name", "code", "created_at"]


class TopicViewSet(AcademicBaseViewSet):
    model = Topic
    serializer_class = TopicSerializer
    queryset = Topic.objects.select_related("school", "subject", "class_level").all()
    filterset_fields = [
        "school",
        "subject",
        "class_level",
        "jamb_relevance_level",
        "is_active",
    ]
    search_fields = ["title", "description", "subject__name", "class_level__name"]
    ordering_fields = ["title", "created_at", "updated_at"]


class TeacherClassSubjectAssignmentViewSet(AcademicBaseViewSet):
    model = TeacherClassSubjectAssignment
    serializer_class = TeacherClassSubjectAssignmentSerializer
    queryset = TeacherClassSubjectAssignment.objects.select_related(
        "school",
        "teacher",
        "class_arm",
        "class_arm__class_level",
        "subject",
        "academic_session",
        "term",
    ).all()
    filterset_fields = [
        "school",
        "teacher",
        "class_arm",
        "subject",
        "academic_session",
        "term",
        "is_active",
    ]
    search_fields = [
        "teacher__full_name",
        "teacher__email",
        "class_arm__name",
        "class_arm__class_level__name",
        "subject__name",
    ]
    ordering_fields = ["created_at", "updated_at"]


class StudentEnrollmentViewSet(AcademicBaseViewSet):
    model = StudentEnrollment
    serializer_class = StudentEnrollmentSerializer
    queryset = StudentEnrollment.objects.select_related(
        "school",
        "student",
        "class_arm",
        "class_arm__class_level",
        "academic_session",
        "term",
    ).all()
    filterset_fields = [
        "school",
        "student",
        "class_arm",
        "academic_session",
        "term",
        "is_active",
    ]
    search_fields = [
        "student__full_name",
        "student__email",
        "class_arm__name",
        "class_arm__class_level__name",
    ]
    ordering_fields = ["created_at", "updated_at"]


class LessonLogViewSet(AcademicBaseViewSet):
    model = LessonLog
    serializer_class = LessonLogSerializer
    queryset = LessonLog.objects.select_related(
        "school",
        "teacher",
        "class_arm",
        "class_arm__class_level",
        "subject",
        "topic",
        "academic_session",
        "term",
    ).all()
    filterset_fields = [
        "school",
        "teacher",
        "class_arm",
        "subject",
        "topic",
        "academic_session",
        "term",
    ]
    search_fields = [
        "teacher__full_name",
        "teacher__email",
        "class_arm__name",
        "class_arm__class_level__name",
        "subject__name",
        "topic__title",
        "notes",
    ]
    ordering_fields = ["taught_at", "created_at", "updated_at"]
