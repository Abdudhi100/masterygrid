from django.db.models import Q

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
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


def is_school_admin(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, "role", None) == UserRole.SCHOOL_ADMIN
    )


def get_user_school(user):
    return getattr(user, "school", None)


def filter_academic_sessions_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()
    return queryset.filter(school=user.school)


def filter_terms_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()
    return queryset.filter(school=user.school)


def filter_class_levels_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()

    if user.role == UserRole.TEACHER:
        return queryset.filter(class_arms__teacher_assignments__teacher=user).distinct()

    if user.role == UserRole.STUDENT:
        return queryset.filter(class_arms__student_enrollments__student=user).distinct()

    return queryset.filter(school=user.school)


def filter_class_arms_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()

    if user.role == UserRole.TEACHER:
        return queryset.filter(teacher_assignments__teacher=user).distinct()

    if user.role == UserRole.STUDENT:
        return queryset.filter(student_enrollments__student=user).distinct()

    return queryset.filter(school=user.school)


def filter_subjects_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.filter(school__isnull=True)

    if user.role == UserRole.TEACHER:
        return queryset.filter(
            Q(school__isnull=True) | Q(teacher_assignments__teacher=user)
        ).distinct()

    return queryset.filter(Q(school__isnull=True) | Q(school=user.school))


def filter_topics_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()

    base_scope = Q(school__isnull=True) | Q(school=user.school)
    class_level_scope = Q(class_level__school=user.school)

    if user.role == UserRole.TEACHER:
        assigned_subjects = TeacherClassSubjectAssignment.objects.filter(
            teacher=user,
            school=user.school,
            is_active=True,
        ).values("subject_id")
        assigned_levels = TeacherClassSubjectAssignment.objects.filter(
            teacher=user,
            school=user.school,
            is_active=True,
        ).values("class_arm__class_level_id")
        return queryset.filter(
            base_scope,
            class_level_scope,
            subject_id__in=assigned_subjects,
            class_level_id__in=assigned_levels,
        ).distinct()

    return queryset.filter(base_scope, class_level_scope)


def filter_teacher_assignments_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()
    if user.role == UserRole.TEACHER:
        return queryset.filter(teacher=user, school=user.school)
    if user.role == UserRole.STUDENT:
        return queryset.none()
    return queryset.filter(school=user.school)


def filter_student_enrollments_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()
    if user.role == UserRole.STUDENT:
        return queryset.filter(student=user, school=user.school)
    return queryset.filter(school=user.school)


def filter_lesson_logs_for_user(queryset, user):
    if is_platform_admin(user):
        return queryset
    if not user.is_authenticated or not user.school_id:
        return queryset.none()
    if user.role == UserRole.TEACHER:
        return queryset.filter(teacher=user, school=user.school)
    if user.role == UserRole.STUDENT:
        enrolled_class_arms = StudentEnrollment.objects.filter(
            student=user,
            school=user.school,
            is_active=True,
        ).values("class_arm_id")
        return queryset.filter(school=user.school, class_arm_id__in=enrolled_class_arms)
    return queryset.filter(school=user.school)


MODEL_FILTERS = {
    AcademicSession: filter_academic_sessions_for_user,
    Term: filter_terms_for_user,
    ClassLevel: filter_class_levels_for_user,
    ClassArm: filter_class_arms_for_user,
    Subject: filter_subjects_for_user,
    Topic: filter_topics_for_user,
    TeacherClassSubjectAssignment: filter_teacher_assignments_for_user,
    StudentEnrollment: filter_student_enrollments_for_user,
    LessonLog: filter_lesson_logs_for_user,
}


def filter_queryset_for_user(queryset, user):
    filter_func = MODEL_FILTERS.get(queryset.model)
    if filter_func is None:
        return queryset.none()
    return filter_func(queryset, user)
