from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel
from apps.question_bank.models import QuestionDifficulty


class AIQuestionSuggestionType(models.TextChoices):
    TOPIC_DIFFICULTY_EXPLANATION = (
        "topic_difficulty_explanation",
        "Topic, Difficulty, and Explanation",
    )
    EXPLANATION_ONLY = "explanation_only", "Explanation Only"
    DIFFICULTY_ONLY = "difficulty_only", "Difficulty Only"
    DUPLICATE_QUALITY_CHECK = "duplicate_quality_check", "Duplicate and Quality Check"


class AIQuestionSuggestionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class AIQuestionSuggestionRun(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="ai_question_suggestion_runs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ai_question_suggestion_runs",
        on_delete=models.PROTECT,
    )
    question = models.ForeignKey(
        "question_bank.Question",
        related_name="ai_suggestion_runs",
        on_delete=models.PROTECT,
    )
    suggestion_type = models.CharField(
        max_length=64,
        choices=AIQuestionSuggestionType.choices,
    )
    status = models.CharField(
        max_length=16,
        choices=AIQuestionSuggestionStatus.choices,
        default=AIQuestionSuggestionStatus.PENDING,
    )
    provider = models.CharField(max_length=64, default="openai")
    model_name = models.CharField(max_length=128)
    prompt_version = models.CharField(max_length=32, default="v1")
    suggested_topic = models.ForeignKey(
        "academics.Topic",
        related_name="ai_question_suggestion_runs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    suggested_difficulty = models.CharField(
        max_length=16,
        choices=QuestionDifficulty.choices,
        null=True,
        blank=True,
    )
    suggested_explanation = models.TextField(blank=True)
    duplicate_warning = models.TextField(blank=True)
    quality_warning = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    applied_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["requested_by", "status"]),
            models.Index(fields=["question", "suggestion_type"]),
        ]

    def __str__(self):
        return f"{self.question_id} - {self.suggestion_type} - {self.status}"

    def clean(self):
        super().clean()

        if (
            self.school_id
            and self.question_id
            and self.question.school_id != self.school_id
        ):
            raise ValidationError(
                {"school": "Suggestion school must match the question school."}
            )

        if self.suggested_topic_id and self.question_id:
            if self.suggested_topic.subject_id != self.question.subject_id:
                raise ValidationError(
                    {"suggested_topic": "Suggested topic must match question subject."}
                )
            if self.suggested_topic.class_level_id != self.question.class_level_id:
                raise ValidationError(
                    {
                        "suggested_topic": (
                            "Suggested topic must match question class level."
                        )
                    }
                )
            if self.question.school_id is None and self.suggested_topic.school_id:
                raise ValidationError(
                    {"suggested_topic": "Global questions must use a global topic."}
                )
            if (
                self.question.school_id
                and self.suggested_topic.school_id
                and self.suggested_topic.school_id != self.question.school_id
            ):
                raise ValidationError(
                    {
                        "suggested_topic": (
                            "Suggested topic must be global or belong to the "
                            "question school."
                        )
                    }
                )

        if self.confidence_score is not None and not 0 <= self.confidence_score <= 1:
            raise ValidationError(
                {"confidence_score": "Confidence score must be between 0 and 1."}
            )
