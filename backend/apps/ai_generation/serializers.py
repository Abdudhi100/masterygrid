from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.ai_generation.models import (
    AIQuestionSuggestionRun,
    AIQuestionSuggestionStatus,
    AIQuestionSuggestionType,
)
from apps.ai_generation.selectors import get_questions_available_for_ai_suggestion
from apps.ai_generation.services import (
    APPLIABLE_FIELDS,
    apply_question_suggestion,
    create_question_suggestion_run,
    process_question_suggestion_run,
)
from apps.question_bank.models import Question
from apps.question_bank.serializers import QuestionSerializer


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    if hasattr(exc, "messages"):
        raise serializers.ValidationError(exc.messages)
    raise serializers.ValidationError(str(exc))


class AIQuestionSuggestionRunSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    requested_by_name = serializers.CharField(
        source="requested_by.full_name",
        read_only=True,
    )
    question_text = serializers.CharField(source="question.question_text", read_only=True)
    question_subject = serializers.CharField(source="question.subject.name", read_only=True)
    question_topic = serializers.CharField(source="question.topic.title", read_only=True)
    question_class_level = serializers.CharField(
        source="question.class_level.name",
        read_only=True,
    )
    suggested_topic_title = serializers.CharField(
        source="suggested_topic.title",
        read_only=True,
    )
    applied_by_name = serializers.CharField(
        source="applied_by.full_name",
        read_only=True,
    )

    class Meta:
        model = AIQuestionSuggestionRun
        fields = [
            "id",
            "school",
            "school_name",
            "requested_by",
            "requested_by_name",
            "question",
            "question_text",
            "question_subject",
            "question_topic",
            "question_class_level",
            "suggestion_type",
            "status",
            "provider",
            "model_name",
            "prompt_version",
            "suggested_topic",
            "suggested_topic_title",
            "suggested_difficulty",
            "suggested_explanation",
            "duplicate_warning",
            "quality_warning",
            "confidence_score",
            "raw_response",
            "error_message",
            "applied_by",
            "applied_by_name",
            "applied_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AIQuestionSuggestionCreateSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.none())
    suggestion_type = serializers.ChoiceField(choices=AIQuestionSuggestionType.values)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        self.fields["question"].queryset = get_questions_available_for_ai_suggestion(user)

    def create(self, validated_data):
        request = self.context["request"]
        try:
            run = create_question_suggestion_run(
                question=validated_data["question"],
                user=request.user,
                suggestion_type=validated_data["suggestion_type"],
            )
            return process_question_suggestion_run(run)
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

    def to_representation(self, instance):
        return AIQuestionSuggestionRunSerializer(
            instance,
            context=self.context,
        ).data


class AIQuestionSuggestionApplySerializer(serializers.Serializer):
    fields_to_apply = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(APPLIABLE_FIELDS)),
        allow_empty=False,
    )

    def validate_fields_to_apply(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Duplicate fields are not allowed.")
        return value

    def save(self, **kwargs):
        request = self.context["request"]
        run = self.context["run"]
        try:
            question, applied_fields = apply_question_suggestion(
                run=run,
                user=request.user,
                fields_to_apply=self.validated_data["fields_to_apply"],
            )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        return {
            "question": QuestionSerializer(question, context=self.context).data,
            "applied_fields": applied_fields,
            "run": AIQuestionSuggestionRunSerializer(run, context=self.context).data,
        }


class AIQuestionSuggestionStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=AIQuestionSuggestionStatus.values,
        read_only=True,
    )
