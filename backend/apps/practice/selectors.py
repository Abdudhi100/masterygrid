import random

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.common.choices import QuestionStatus, UserRole
from apps.practice.models import PracticeDifficulty, PracticeSession
from apps.question_bank.models import Question


def get_practice_sessions_for_user(user):
    queryset = PracticeSession.objects.select_related(
        "school",
        "student",
        "subject",
        "topic",
        "class_level",
        "class_arm",
    ).prefetch_related(
        "session_questions",
        "session_questions__question",
        "answers",
    )

    if not user or not user.is_authenticated:
        return queryset.none()

    if user.role == UserRole.STUDENT and user.school_id:
        return queryset.filter(school=user.school, student=user)

    return queryset.none()


def get_practice_session_for_user(user, session_id):
    return get_object_or_404(get_practice_sessions_for_user(user), pk=session_id)


def get_available_practice_questions(
    student,
    subject,
    topic=None,
    class_level=None,
    difficulty=PracticeDifficulty.MIXED,
    count=10,
):
    if not student or not student.is_authenticated or student.role != UserRole.STUDENT:
        raise ValidationError({"student": "Only students can practise questions."})

    if count <= 0:
        raise ValidationError({"question_count": "Question count must be positive."})

    queryset = Question.objects.filter(
        Q(school__isnull=True) | Q(school=student.school),
        subject=subject,
        status=QuestionStatus.APPROVED,
        is_active=True,
    ).select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
    ).prefetch_related("options")

    if topic is not None:
        queryset = queryset.filter(topic=topic)

    if class_level is not None:
        queryset = queryset.filter(class_level=class_level)

    if difficulty != PracticeDifficulty.MIXED:
        queryset = queryset.filter(difficulty=difficulty)

    available_count = queryset.count()
    if available_count < count:
        raise ValidationError(
            {
                "question_count": (
                    f"Only {available_count} approved active question(s) are "
                    f"available for this practice request; {count} requested."
                )
            }
        )

    questions = list(queryset)
    random.shuffle(questions)
    return questions[:count]
