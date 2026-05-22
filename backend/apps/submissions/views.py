from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.submissions.filters import SubmissionFilter
from apps.submissions.models import Submission
from apps.submissions.permissions import SubmissionPermission
from apps.submissions.selectors import (
    get_student_assignments,
    get_submission_queryset_for_user,
)
from apps.submissions.serializers import (
    StudentAssignmentListSerializer,
    SubmissionResultSerializer,
    SubmissionSerializer,
    SubmissionStartInputSerializer,
    SubmissionStartSerializer,
    SubmissionSubmitSerializer,
)


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    model = Submission
    serializer_class = SubmissionSerializer
    permission_classes = [SubmissionPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubmissionFilter
    search_fields = [
        "assignment__title",
        "student__full_name",
        "student__email",
    ]
    ordering_fields = ["created_at", "updated_at", "submitted_at", "graded_at", "score"]

    def get_queryset(self):
        return get_submission_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        if self.action == "result":
            return SubmissionResultSerializer
        return SubmissionSerializer

    @action(detail=False, methods=["post"], url_path="start-assignment")
    def start_assignment(self, request):
        input_serializer = SubmissionStartInputSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        input_serializer.is_valid(raise_exception=True)
        submission = input_serializer.save()
        response_serializer = SubmissionStartSerializer(
            submission,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="my-assignments")
    def my_assignments(self, request):
        assignments = get_student_assignments(request.user)
        serializer = StudentAssignmentListSerializer(
            assignments,
            many=True,
            context={"request": request, "student": request.user},
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        submission = self.get_object()
        serializer = SubmissionSubmitSerializer(
            data=request.data,
            context={"request": request, "submission": submission},
        )
        serializer.is_valid(raise_exception=True)
        graded_submission = serializer.save()
        response_serializer = SubmissionResultSerializer(
            graded_submission,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)

    @action(detail=True, methods=["get"])
    def result(self, request, pk=None):
        submission = self.get_object()
        serializer = SubmissionResultSerializer(
            submission,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
