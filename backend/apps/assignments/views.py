from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.assignments.filters import AssignmentFilter
from apps.assignments.models import Assignment
from apps.assignments.permissions import AssignmentPermission
from apps.assignments.selectors import get_assignment_queryset_for_user, is_platform_admin
from apps.assignments.serializers import (
    AssignmentCreateUpdateSerializer,
    AssignmentDeadlineActionSerializer,
    AssignmentGenerateFromTopicSerializer,
    AssignmentReopenSerializer,
    AssignmentSerializer,
)
from apps.assignments.services import (
    archive_assignment,
    close_assignment,
    extend_assignment_deadline,
    publish_assignment,
    reopen_assignment,
)
from apps.common.choices import UserRole


class AssignmentViewSet(viewsets.ModelViewSet):
    model = Assignment
    permission_classes = [AssignmentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AssignmentFilter
    search_fields = ["title", "instructions"]
    ordering_fields = ["created_at", "updated_at", "starts_at", "due_at", "published_at"]

    def get_queryset(self):
        return get_assignment_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return AssignmentCreateUpdateSerializer
        if self.action == "generate_from_topic":
            return AssignmentGenerateFromTopicSerializer
        return AssignmentSerializer

    def perform_create(self, serializer):
        user = self.request.user
        save_kwargs = {}

        if user.role == UserRole.TEACHER:
            save_kwargs["teacher"] = user
            save_kwargs["school"] = user.school
        elif user.role == UserRole.SCHOOL_ADMIN and not is_platform_admin(user):
            save_kwargs["school"] = user.school

        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        user = self.request.user
        save_kwargs = {}

        if user.role == UserRole.TEACHER:
            save_kwargs["teacher"] = user
            save_kwargs["school"] = user.school
        elif user.role == UserRole.SCHOOL_ADMIN and not is_platform_admin(user):
            save_kwargs["school"] = user.school

        serializer.save(**save_kwargs)

    def destroy(self, request, *args, **kwargs):
        assignment = self.get_object()
        archived_assignment = archive_assignment(assignment, request.user)
        serializer = AssignmentSerializer(
            archived_assignment,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="generate-from-topic")
    def generate_from_topic(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()
        response_serializer = AssignmentSerializer(
            assignment,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        assignment = self.get_object()
        published_assignment = publish_assignment(assignment, request.user)
        serializer = AssignmentSerializer(
            published_assignment,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        assignment = self.get_object()
        closed_assignment = close_assignment(assignment, request.user)
        serializer = AssignmentSerializer(
            closed_assignment,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="extend-deadline")
    def extend_deadline(self, request, pk=None):
        assignment = self.get_object()
        input_serializer = AssignmentDeadlineActionSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        updated_assignment = extend_assignment_deadline(
            assignment=assignment,
            user=request.user,
            due_at=input_serializer.validated_data["due_at"],
            allow_late_submissions=input_serializer.validated_data.get(
                "allow_late_submissions",
            ),
            late_submission_deadline=input_serializer.validated_data.get(
                "late_submission_deadline",
            ),
        )
        serializer = AssignmentSerializer(
            updated_assignment,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        assignment = self.get_object()
        input_serializer = AssignmentReopenSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        updated_assignment = reopen_assignment(
            assignment=assignment,
            user=request.user,
            due_at=input_serializer.validated_data.get("due_at"),
            allow_late_submissions=input_serializer.validated_data.get(
                "allow_late_submissions",
            ),
            late_submission_deadline=input_serializer.validated_data.get(
                "late_submission_deadline",
            ),
        )
        serializer = AssignmentSerializer(
            updated_assignment,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        assignment = self.get_object()
        archived_assignment = archive_assignment(assignment, request.user)
        serializer = AssignmentSerializer(
            archived_assignment,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
