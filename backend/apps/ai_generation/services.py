from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.academics.models import Topic
from apps.ai_generation.models import (
    AIQuestionSuggestionRun,
    AIQuestionSuggestionStatus,
    AIQuestionSuggestionType,
)
from apps.ai_generation.providers.openai import (
    AIProviderError,
    call_openai_question_suggestion,
)
from apps.question_bank.models import QuestionDifficulty


APPLIABLE_FIELDS = {"topic", "difficulty", "explanation"}


def _option_lines(question):
    return [
        f"{option.label}. {option.text}"
        for option in question.options.all().order_by("label")
    ]


def _available_topic_titles(question):
    queryset = Topic.objects.filter(
        Q(school__isnull=True) | Q(school=question.school),
        subject=question.subject,
        class_level=question.class_level,
        is_active=True,
    ).order_by("title")
    return [topic.title for topic in queryset]


def build_question_suggestion_prompt(question, suggestion_type):
    available_topics = _available_topic_titles(question)
    option_text = "\n".join(_option_lines(question)) or "No options were found."
    current_topic = question.topic.title if question.topic_id else "Unknown"
    source_name = question.source.name if question.source_id else "Unknown"
    instructions = {
        AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION: (
            "Suggest the best existing topic, estimate difficulty, write a clear "
            "explanation, and flag duplicate or quality concerns."
        ),
        AIQuestionSuggestionType.EXPLANATION_ONLY: (
            "Write or improve only the explanation and flag quality concerns."
        ),
        AIQuestionSuggestionType.DIFFICULTY_ONLY: (
            "Estimate only the difficulty and flag quality concerns."
        ),
        AIQuestionSuggestionType.DUPLICATE_QUALITY_CHECK: (
            "Focus on duplicate risk and quality warnings. Do not rewrite the question."
        ),
    }

    return "\n".join(
        [
            instructions.get(
                suggestion_type,
                instructions[AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION],
            ),
            "",
            "Use only one of these existing topic titles when suggesting a topic:",
            ", ".join(available_topics) or "No active topics available.",
            "",
            f"Subject: {question.subject.name}",
            f"Class level: {question.class_level.name}",
            f"Current topic: {current_topic}",
            f"Current difficulty: {question.difficulty}",
            f"Source: {source_name}",
            "",
            "Question:",
            question.question_text,
            "",
            "Options:",
            option_text,
            "",
            "Existing explanation:",
            question.explanation or "None",
        ]
    )


def question_suggestion_response_schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "suggested_topic_title": {"type": "string"},
            "suggested_difficulty": {
                "type": "string",
                "enum": ["", *QuestionDifficulty.values],
            },
            "suggested_explanation": {"type": "string"},
            "duplicate_warning": {"type": "string"},
            "quality_warning": {"type": "string"},
            "confidence_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
        },
        "required": [
            "suggested_topic_title",
            "suggested_difficulty",
            "suggested_explanation",
            "duplicate_warning",
            "quality_warning",
            "confidence_score",
        ],
    }


def call_openai_for_question_suggestion(question, suggestion_type):
    prompt = build_question_suggestion_prompt(question, suggestion_type)
    return call_openai_question_suggestion(
        prompt=prompt,
        response_schema=question_suggestion_response_schema(),
        model_name=settings.OPENAI_MODEL,
    )


def validate_ai_suggestion_payload(payload, suggestion_type=None):
    if not isinstance(payload, dict):
        raise ValidationError("AI response must be a JSON object.")

    normalized = {
        "suggested_topic_title": str(payload.get("suggested_topic_title", "")).strip(),
        "suggested_difficulty": str(payload.get("suggested_difficulty", ""))
        .strip()
        .lower(),
        "suggested_explanation": str(payload.get("suggested_explanation", "")).strip(),
        "duplicate_warning": str(payload.get("duplicate_warning", "")).strip(),
        "quality_warning": str(payload.get("quality_warning", "")).strip(),
        "confidence_score": payload.get("confidence_score"),
    }

    difficulty = normalized["suggested_difficulty"]
    if difficulty and difficulty not in QuestionDifficulty.values:
        raise ValidationError("Suggested difficulty must be easy, medium, or hard.")

    if normalized["confidence_score"] is not None:
        try:
            normalized["confidence_score"] = float(normalized["confidence_score"])
        except (TypeError, ValueError) as exc:
            raise ValidationError("Confidence score must be numeric.") from exc
        if not 0 <= normalized["confidence_score"] <= 1:
            raise ValidationError("Confidence score must be between 0 and 1.")

    if suggestion_type in {
        AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION,
        AIQuestionSuggestionType.EXPLANATION_ONLY,
    } and not normalized["suggested_explanation"]:
        raise ValidationError("Suggested explanation cannot be blank.")

    if suggestion_type in {
        AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION,
        AIQuestionSuggestionType.DIFFICULTY_ONLY,
    } and not difficulty:
        raise ValidationError("Suggested difficulty cannot be blank.")

    return normalized


def match_suggested_topic(question, suggested_topic_title):
    if not suggested_topic_title:
        return None

    queryset = Topic.objects.filter(
        Q(school__isnull=True) | Q(school=question.school),
        subject=question.subject,
        class_level=question.class_level,
        title__iexact=suggested_topic_title,
        is_active=True,
    )

    if question.school_id:
        school_topic = queryset.filter(school=question.school).first()
        if school_topic:
            return school_topic

    return queryset.filter(school__isnull=True).first()


def create_question_suggestion_run(question, user, suggestion_type):
    window_start = timezone.now() - timedelta(days=1)
    request_count = AIQuestionSuggestionRun.objects.filter(
        requested_by=user,
        created_at__gte=window_start,
    ).count()
    if request_count >= settings.AI_DAILY_REQUEST_LIMIT_PER_USER:
        raise ValidationError("Daily AI suggestion limit reached for this user.")

    run = AIQuestionSuggestionRun(
        school=question.school,
        requested_by=user,
        question=question,
        suggestion_type=suggestion_type,
        model_name=settings.OPENAI_MODEL,
    )
    run.full_clean()
    run.save()
    return run


def _mark_run_failed(run, message):
    run.status = AIQuestionSuggestionStatus.FAILED
    run.error_message = str(message)
    run.completed_at = timezone.now()
    run.full_clean()
    run.save(
        update_fields=[
            "status",
            "error_message",
            "completed_at",
            "updated_at",
        ]
    )
    return run


@transaction.atomic
def process_question_suggestion_run(run):
    run.status = AIQuestionSuggestionStatus.PROCESSING
    run.error_message = ""
    run.full_clean()
    run.save(update_fields=["status", "error_message", "updated_at"])

    if not settings.AI_GENERATION_ENABLED:
        return _mark_run_failed(run, "AI generation is disabled.")

    try:
        payload, raw_response = call_openai_for_question_suggestion(
            run.question,
            run.suggestion_type,
        )
        suggestion = validate_ai_suggestion_payload(payload, run.suggestion_type)
    except (AIProviderError, ValidationError) as exc:
        return _mark_run_failed(run, exc)

    run.suggested_topic = match_suggested_topic(
        run.question,
        suggestion["suggested_topic_title"],
    )
    run.suggested_difficulty = suggestion["suggested_difficulty"] or None
    run.suggested_explanation = suggestion["suggested_explanation"]
    run.duplicate_warning = suggestion["duplicate_warning"]
    run.quality_warning = suggestion["quality_warning"]
    run.confidence_score = suggestion["confidence_score"]
    run.raw_response = raw_response if settings.AI_STORE_RAW_PROVIDER_RESPONSE else None
    run.status = AIQuestionSuggestionStatus.SUCCEEDED
    run.error_message = ""
    run.completed_at = timezone.now()
    run.full_clean()
    run.save()
    return run


@transaction.atomic
def apply_question_suggestion(run, user, fields_to_apply):
    fields = set(fields_to_apply)
    invalid_fields = fields - APPLIABLE_FIELDS
    if invalid_fields:
        raise ValidationError(f"Unsupported fields: {', '.join(sorted(invalid_fields))}.")

    if run.status != AIQuestionSuggestionStatus.SUCCEEDED:
        raise ValidationError("Only succeeded AI suggestion runs can be applied.")

    question = run.question
    applied_fields = []

    if "topic" in fields:
        if not run.suggested_topic_id:
            raise ValidationError("This run has no matched topic suggestion to apply.")
        question.topic = run.suggested_topic
        applied_fields.append("topic")

    if "difficulty" in fields:
        if not run.suggested_difficulty:
            raise ValidationError("This run has no difficulty suggestion to apply.")
        question.difficulty = run.suggested_difficulty
        applied_fields.append("difficulty")

    if "explanation" in fields:
        if not run.suggested_explanation:
            raise ValidationError("This run has no explanation suggestion to apply.")
        question.explanation = run.suggested_explanation
        applied_fields.append("explanation")

    if not applied_fields:
        raise ValidationError("At least one supported field must be applied.")

    question.full_clean()
    question.save(update_fields=[*applied_fields, "updated_at"])

    run.applied_by = user
    run.applied_at = timezone.now()
    run.full_clean()
    run.save(update_fields=["applied_by", "applied_at", "updated_at"])

    return question, applied_fields
