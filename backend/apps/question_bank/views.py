from django.conf import settings
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.filters import QuestionFilter
from apps.question_bank.models import Question, QuestionImportBatch, QuestionSource
from apps.question_bank.permissions import (
    CanImportQuestions,
    CanSearchApprovedQuestions,
    CanViewQuestionImports,
    QuestionBankPermission,
)
from apps.question_bank.selectors import get_question_queryset_for_user, is_platform_admin
from apps.question_bank.serializers import (
    ApprovedQuestionSearchSerializer,
    QuestionImportBatchSerializer,
    QuestionImportCreateSerializer,
    QuestionImportRowSerializer,
    QuestionCreateUpdateSerializer,
    QuestionSerializer,
    QuestionSourceSerializer,
)
from apps.question_bank.services import (
    approve_question,
    archive_question,
    process_question_import_batch,
    reject_question,
)


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

    def get_permissions(self):
        if self.action == "search_approved":
            return [CanSearchApprovedQuestions()]
        return super().get_permissions()

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

    @action(detail=False, methods=["get"], url_path="search-approved")
    def search_approved(self, request):
        serializer = ApprovedQuestionSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters_data = serializer.validated_data
        user = request.user

        queryset = Question.objects.filter(
            status=QuestionStatus.APPROVED,
            is_active=True,
        ).select_related(
            "school",
            "subject",
            "topic",
            "class_level",
            "source",
            "created_by",
            "reviewed_by",
        ).prefetch_related("options")

        if not is_platform_admin(user):
            queryset = queryset.filter(Q(school__isnull=True) | Q(school=user.school))

        if "subject" in filters_data:
            queryset = queryset.filter(subject_id=filters_data["subject"])
        if "topic" in filters_data:
            queryset = queryset.filter(topic_id=filters_data["topic"])
        if "class_level" in filters_data:
            queryset = queryset.filter(class_level_id=filters_data["class_level"])
        if "difficulty" in filters_data:
            queryset = queryset.filter(difficulty=filters_data["difficulty"])
        if "source_type" in filters_data:
            queryset = queryset.filter(source__source_type=filters_data["source_type"])
        if filters_data.get("exam_body"):
            queryset = queryset.filter(source__exam_body__iexact=filters_data["exam_body"])
        if "year" in filters_data:
            queryset = queryset.filter(source__year=filters_data["year"])

        available_count = queryset.count()
        requested_count = filters_data.get("count")
        if filters_data.get("random"):
            queryset = queryset.order_by("?")
        else:
            queryset = queryset.order_by("-created_at")
        if requested_count:
            queryset = queryset[:requested_count]

        questions = list(queryset)
        message = ""
        if requested_count and available_count < requested_count:
            message = (
                f"Only {available_count} approved active question(s) are available "
                f"for the requested filters; {requested_count} requested."
            )

        question_serializer = QuestionSerializer(
            questions,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(
            {
                "available_count": available_count,
                "requested_count": requested_count,
                "returned_count": len(questions),
                "message": message,
                "results": question_serializer.data,
            }
        )


class QuestionImportBatchViewSet(viewsets.ModelViewSet):
    model = QuestionImportBatch
    serializer_class = QuestionImportBatchSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "head", "options"]
    allow_teacher_imports = getattr(settings, "QUESTION_IMPORT_ALLOW_TEACHERS", False)

    def get_permissions(self):
        if self.action == "create":
            return [CanImportQuestions()]
        return [CanViewQuestionImports()]

    def get_serializer_class(self):
        if self.action == "create":
            return QuestionImportCreateSerializer
        return QuestionImportBatchSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["allow_teacher_imports"] = self.allow_teacher_imports
        return context

    def get_queryset(self):
        queryset = QuestionImportBatch.objects.select_related(
            "school",
            "uploaded_by",
            "source",
        )
        user = self.request.user
        if is_platform_admin(user):
            return queryset

        if not user or not user.is_authenticated or not user.school_id:
            return queryset.none()

        if user.role == UserRole.SCHOOL_ADMIN:
            return queryset.filter(school=user.school)

        if user.role == UserRole.TEACHER:
            return queryset.filter(school=user.school, uploaded_by=user)

        return queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        batch = process_question_import_batch(batch)
        output_serializer = QuestionImportBatchSerializer(
            batch,
            context=self.get_serializer_context(),
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def rows(self, request, pk=None):
        batch = self.get_object()
        queryset = batch.rows.select_related("question").order_by("row_number")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = QuestionImportRowSerializer(
                page,
                many=True,
                context=self.get_serializer_context(),
            )
            return self.get_paginated_response(serializer.data)

        serializer = QuestionImportRowSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
