from django.db.models import Q

from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(user, "is_superuser", False)
        )
    )


def get_question_queryset_for_user(user):
    base_queryset = Question.objects.select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
        "created_by",
        "reviewed_by",
    ).prefetch_related("options")

    if is_platform_admin(user):
        return base_queryset

    if not user or not user.is_authenticated:
        return base_queryset.none()

    if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
        return base_queryset.filter(Q(school__isnull=True) | Q(school=user.school))

    if user.role == UserRole.TEACHER and user.school_id:
        return base_queryset.filter(
            Q(school__isnull=True, status=QuestionStatus.APPROVED, is_active=True)
            | Q(school=user.school)
        )

    return base_queryset.none()


def get_approved_global_and_school_questions(user):
    if not user or not user.is_authenticated or not user.school_id:
        return Question.objects.none()

    return Question.objects.filter(
        Q(school__isnull=True) | Q(school=user.school),
        status=QuestionStatus.APPROVED,
        is_active=True,
    ).select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
    ).prefetch_related("options")


def get_questions_by_topic(
    *,
    school,
    subject,
    topic,
    class_level,
    approved_only=True,
):
    queryset = Question.objects.filter(
        Q(school__isnull=True) | Q(school=school),
        subject=subject,
        topic=topic,
        class_level=class_level,
    )

    if approved_only:
        queryset = queryset.filter(status=QuestionStatus.APPROVED, is_active=True)

    return queryset.select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
    ).prefetch_related("options")
