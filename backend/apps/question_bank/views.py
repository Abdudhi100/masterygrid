from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.filters import QuestionFilter
from apps.question_bank.models import Question, QuestionSource
from apps.question_bank.permissions import QuestionBankPermission
from apps.question_bank.selectors import get_question_queryset_for_user, is_platform_admin
from apps.question_bank.serializers import (
    QuestionCreateUpdateSerializer,
    QuestionSerializer,
    QuestionSourceSerializer,
)
from apps.question_bank.services import approve_question, archive_question, reject_question


class QuestionSourceViewSet(viewsets.ModelViewSet):
    model = QuestionSource
    serializer_class = QuestionSourceSerializer
    permission_classes = [QuestionBankPermission]
    queryset = QuestionSource.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["source_type", "exam_body", "year", "is_active"]
    search_fields = ["name", "exam_body", "description"]
    ordering_fields = ["name", "year", "created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_platform_admin(self.request.user):
            return queryset
        return queryset.filter(is_active=True)


class QuestionViewSet(viewsets.ModelViewSet):
    model = Question
    permission_classes = [QuestionBankPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = QuestionFilter
    search_fields = ["question_text", "explanation"]
    ordering_fields = ["created_at", "updated_at", "difficulty", "status"]

    def get_queryset(self):
        return get_question_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return QuestionCreateUpdateSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        user = self.request.user
        save_kwargs = {"created_by": user}

        if not is_platform_admin(user):
            save_kwargs["school"] = user.school

        if user.role == UserRole.TEACHER:
            save_kwargs["status"] = QuestionStatus.DRAFT

        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        user = self.request.user
        save_kwargs = {}

        if not is_platform_admin(user):
            save_kwargs["school"] = user.school

        if user.role == UserRole.TEACHER:
            save_kwargs["status"] = QuestionStatus.DRAFT

        serializer.save(**save_kwargs)

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        archived_question = archive_question(question, request.user)
        serializer = self.get_serializer(archived_question)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        question = self.get_object()
        approved_question = approve_question(question, request.user)
        serializer = QuestionSerializer(approved_question, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        question = self.get_object()
        rejected_question = reject_question(question, request.user)
        serializer = QuestionSerializer(rejected_question, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        question = self.get_object()
        archived_question = archive_question(question, request.user)
        serializer = QuestionSerializer(archived_question, context=self.get_serializer_context())
        return Response(serializer.data)
