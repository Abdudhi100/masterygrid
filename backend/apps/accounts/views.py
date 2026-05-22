from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import StudentProfile, TeacherProfile
from apps.accounts.permissions import (
    IsProfileOwnerOrSchoolAdmin,
    IsSchoolUserManager,
    is_platform_admin,
)
from apps.accounts.serializers import (
    CurrentUserSerializer,
    RegisterUserSerializer,
    StudentListSerializer,
    StudentProfileSerializer,
    TeacherListSerializer,
    TeacherProfileSerializer,
)
from apps.common.choices import UserRole

User = get_user_model()


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [IsSchoolUserManager]


class SchoolScopedUserListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsSchoolUserManager]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["school", "is_active"]
    search_fields = ["full_name", "email", "school__name"]
    ordering_fields = ["full_name", "email", "created_at"]
    ordering = ["full_name", "email"]
    role = None

    def get_queryset(self):
        queryset = User.objects.filter(role=self.role).select_related(
            "school",
            "teacher_profile",
            "student_profile",
        )

        if is_platform_admin(self.request.user):
            return queryset

        return queryset.filter(school=self.request.user.school)


class TeacherViewSet(SchoolScopedUserListViewSet):
    serializer_class = TeacherListSerializer
    role = UserRole.TEACHER


class StudentViewSet(SchoolScopedUserListViewSet):
    serializer_class = StudentListSerializer
    role = UserRole.STUDENT


class ProfileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsProfileOwnerOrSchoolAdmin]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["school", "user"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["user__full_name"]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if is_platform_admin(user):
            return queryset

        if user.role == UserRole.SCHOOL_ADMIN:
            return queryset.filter(school=user.school)

        return queryset.filter(user=user)

    def get_save_kwargs(self):
        user = self.request.user
        if is_platform_admin(user):
            return {}

        if user.role == UserRole.SCHOOL_ADMIN:
            return {"school": user.school}

        return {}

    def perform_create(self, serializer):
        serializer.save(**self.get_save_kwargs())

    def perform_update(self, serializer):
        serializer.save(**self.get_save_kwargs())


class TeacherProfileViewSet(ProfileViewSet):
    serializer_class = TeacherProfileSerializer
    queryset = TeacherProfile.objects.select_related("user", "school").all()
    search_fields = [
        "user__full_name",
        "user__email",
        "staff_id",
        "phone_number",
        "school__name",
    ]


class StudentProfileViewSet(ProfileViewSet):
    serializer_class = StudentProfileSerializer
    queryset = StudentProfile.objects.select_related("user", "school").all()
    search_fields = [
        "user__full_name",
        "user__email",
        "admission_number",
        "guardian_name",
        "guardian_phone",
        "school__name",
    ]
