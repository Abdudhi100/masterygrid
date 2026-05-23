from django.conf import settings

from apps.ai_generation.models import AIQuestionSuggestionRun
from apps.common.choices import UserRole
from apps.question_bank.models import Question
from apps.question_bank.selectors import is_platform_admin


def get_ai_question_suggestions_for_user(user):
    queryset = AIQuestionSuggestionRun.objects.select_related(
        "school",
        "requested_by",
        "question",
        "question__subject",
        "question__topic",
        "question__class_level",
        "suggested_topic",
        "applied_by",
    )

    if is_platform_admin(user):
        return queryset

    if not user or not user.is_authenticated or not user.school_id:
        return queryset.none()

    if user.role == UserRole.SCHOOL_ADMIN:
        return queryset.filter(school=user.school)

    if (
        user.role == UserRole.TEACHER
        and settings.AI_ALLOW_TEACHER_SUGGESTIONS
    ):
        return queryset.filter(school=user.school, requested_by=user)

    return queryset.none()


def get_questions_available_for_ai_suggestion(user):
    queryset = Question.objects.select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
        "created_by",
        "reviewed_by",
    ).prefetch_related("options")

    if is_platform_admin(user):
        return queryset

    if not user or not user.is_authenticated or not user.school_id:
        return queryset.none()

    if user.role == UserRole.SCHOOL_ADMIN:
        return queryset.filter(school=user.school)

    if (
        user.role == UserRole.TEACHER
        and settings.AI_ALLOW_TEACHER_SUGGESTIONS
    ):
        return queryset.filter(school=user.school)

    return queryset.none()
