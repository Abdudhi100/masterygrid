from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.imports import (
    build_user_import_preflight_report,
    process_user_import,
)
from apps.accounts.models import StudentProfile, TeacherProfile, UserImportBatch
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
    UserImportBatchSerializer,
    UserImportRowSerializer,
    UserImportUploadSerializer,
)
from apps.common.choices import UserRole

User = get_user_model()


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    if hasattr(exc, "messages"):
        raise ValidationError(exc.messages)
    raise ValidationError(str(exc))


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


class UserImportQuerysetMixin:
    def get_queryset(self):
        queryset = UserImportBatch.objects.select_related(
            "school",
            "uploaded_by",
        ).prefetch_related("rows")
        user = self.request.user
        if is_platform_admin(user):
            return queryset
        if user and user.is_authenticated and user.role == UserRole.SCHOOL_ADMIN:
            return queryset.filter(school=user.school)
        return queryset.none()


class UserImportPreflightView(APIView):
    permission_classes = [IsSchoolUserManager]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UserImportUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            report = build_user_import_preflight_report(
                uploaded_file=serializer.validated_data["file"],
                import_type=serializer.validated_data["import_type"],
                school=serializer.validated_data["school"],
            )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
        return Response(report)


class UserImportListCreateView(UserImportQuerysetMixin, APIView):
    permission_classes = [IsSchoolUserManager]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        queryset = self.get_queryset()
        import_type = request.query_params.get("import_type")
        if import_type:
            queryset = queryset.filter(import_type=import_type)
        serializer = UserImportBatchSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserImportUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            batch = process_user_import(
                uploaded_file=serializer.validated_data["file"],
                import_type=serializer.validated_data["import_type"],
                school=serializer.validated_data["school"],
                uploaded_by=request.user,
            )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
        output_serializer = UserImportBatchSerializer(batch)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class UserImportDetailView(UserImportQuerysetMixin, APIView):
    permission_classes = [IsSchoolUserManager]

    def get(self, request, pk):
        batch = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UserImportBatchSerializer(batch)
        return Response(serializer.data)


class UserImportRowsView(UserImportQuerysetMixin, APIView):
    permission_classes = [IsSchoolUserManager]

    def get(self, request, pk):
        batch = get_object_or_404(self.get_queryset(), pk=pk)
        rows = batch.rows.select_related("user").order_by("row_number")
        serializer = UserImportRowSerializer(rows, many=True)
        return Response(serializer.data)
