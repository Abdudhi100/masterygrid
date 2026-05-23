from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai_generation.permissions import (
    CanApplyQuestionAISuggestion,
    CanRequestQuestionAISuggestion,
)
from apps.ai_generation.selectors import get_ai_question_suggestions_for_user
from apps.ai_generation.serializers import (
    AIQuestionSuggestionApplySerializer,
    AIQuestionSuggestionCreateSerializer,
    AIQuestionSuggestionRunSerializer,
)


class AIQuestionSuggestionRunViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["suggestion_type", "status", "question", "school"]
    ordering_fields = ["created_at", "completed_at", "applied_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return get_ai_question_suggestions_for_user(self.request.user)

    def get_permissions(self):
        if self.action == "apply":
            return [CanApplyQuestionAISuggestion()]
        return [CanRequestQuestionAISuggestion()]

    def get_serializer_class(self):
        if self.action == "create":
            return AIQuestionSuggestionCreateSerializer
        if self.action == "apply":
            return AIQuestionSuggestionApplySerializer
        return AIQuestionSuggestionRunSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = serializer.save()
        output_serializer = AIQuestionSuggestionRunSerializer(
            run,
            context=self.get_serializer_context(),
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        run = self.get_object()
        self.check_object_permissions(request, run)
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "run": run},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_200_OK)
