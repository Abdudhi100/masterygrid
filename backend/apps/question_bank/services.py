from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.common.choices import QuestionStatus, UserRole
from apps.common.constants import JAMB_MVP_OPTION_COUNT
from apps.question_bank.models import Question, QuestionOptionLabel


EXPECTED_OPTION_LABELS = {"A", "B", "C", "D"}


def validate_question_options(options):
    if len(options) != JAMB_MVP_OPTION_COUNT:
        raise ValidationError(
            {"options": f"Exactly {JAMB_MVP_OPTION_COUNT} options are required."}
        )

    labels = [option.get("label") for option in options]
    label_set = set(labels)
    if label_set != EXPECTED_OPTION_LABELS:
        raise ValidationError({"options": "Options must use labels A, B, C, and D."})

    correct_count = sum(1 for option in options if option.get("is_correct") is True)
    if correct_count != 1:
        raise ValidationError({"options": "Exactly one option must be marked correct."})

    normalized_texts = []
    for option in options:
        text = option.get("text", "")
        if not text or not text.strip():
            raise ValidationError({"options": "Option text cannot be blank."})
        normalized_texts.append(text.strip().casefold())

    if len(normalized_texts) != len(set(normalized_texts)):
        raise ValidationError(
            {"options": "Duplicate option text is not allowed for the same question."}
        )


def can_review_question(question, reviewer):
    if not reviewer or not reviewer.is_authenticated:
        return False

    if reviewer.role == UserRole.PLATFORM_ADMIN or reviewer.is_superuser:
        return True

    return (
        reviewer.role == UserRole.SCHOOL_ADMIN
        and question.school_id is not None
        and question.school_id == reviewer.school_id
    )


@transaction.atomic
def approve_question(question, reviewer):
    if not can_review_question(question, reviewer):
        raise PermissionDenied("You do not have permission to approve this question.")

    question.status = QuestionStatus.APPROVED
    question.reviewed_by = reviewer
    question.reviewed_at = timezone.now()
    question.is_active = True
    question.full_clean()
    validate_persisted_question_options(question)
    question.save(update_fields=["status", "reviewed_by", "reviewed_at", "is_active", "updated_at"])
    return question


@transaction.atomic
def reject_question(question, reviewer):
    if not can_review_question(question, reviewer):
        raise PermissionDenied("You do not have permission to reject this question.")

    question.status = QuestionStatus.REJECTED
    question.reviewed_by = reviewer
    question.reviewed_at = timezone.now()
    question.full_clean()
    question.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
    return question


@transaction.atomic
def archive_question(question, user):
    if not can_review_question(question, user):
        raise PermissionDenied("You do not have permission to archive this question.")

    question.status = QuestionStatus.ARCHIVED
    question.is_active = False
    question.full_clean()
    question.save(update_fields=["status", "is_active", "updated_at"])
    return question


def validate_persisted_question_options(question):
    options = list(question.options.values("label", "text", "is_correct"))
    validate_question_options(options)


def get_approved_questions_for_topic(
    *,
    school,
    subject,
    topic,
    class_level,
    limit=None,
):
    queryset = (
        Question.objects.filter(
            status=QuestionStatus.APPROVED,
            is_active=True,
            subject=subject,
            topic=topic,
            class_level=class_level,
        )
        .filter(school__isnull=True)
        | Question.objects.filter(
            status=QuestionStatus.APPROVED,
            is_active=True,
            school=school,
            subject=subject,
            topic=topic,
            class_level=class_level,
        )
    )
    queryset = queryset.select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
    ).prefetch_related("options").order_by("-created_at")

    if limit is not None:
        return queryset[:limit]
    return queryset


def import_questions_from_csv(*args, **kwargs):
    raise NotImplementedError("CSV import will be implemented after the core MVP workflow.")
