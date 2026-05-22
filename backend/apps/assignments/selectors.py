from django.shortcuts import get_object_or_404

from apps.assignments.models import Assignment
from apps.common.choices import UserRole


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(user, "is_superuser", False)
        )
    )


def get_assignment_queryset_for_user(user):
    queryset = Assignment.objects.select_related(
        "school",
        "teacher",
        "class_arm",
        "class_arm__class_level",
        "subject",
        "topic",
        "lesson_log",
    ).prefetch_related(
        "assignment_questions",
        "assignment_questions__question",
        "assignment_questions__question__source",
    )

    if is_platform_admin(user):
        return queryset

    if not user or not user.is_authenticated:
        return queryset.none()

    if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
        return queryset.filter(school=user.school)

    if user.role == UserRole.TEACHER and user.school_id:
        return queryset.filter(school=user.school, teacher=user)

    return get_student_visible_assignments_placeholder(user)


def get_teacher_assignments(user):
    if not user or not user.is_authenticated or user.role != UserRole.TEACHER:
        return Assignment.objects.none()
    return get_assignment_queryset_for_user(user)


def get_student_visible_assignments_placeholder(user):
    return Assignment.objects.none()


def get_assignment_detail_for_user(user, assignment_id):
    queryset = get_assignment_queryset_for_user(user)
    return get_object_or_404(queryset, pk=assignment_id)
