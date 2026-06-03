from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from apps.academics.models import StudentEnrollment
from apps.assignments.models import Assignment
from apps.common.choices import AssignmentStatus, UserRole
from apps.submissions.models import Submission


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(user, "is_superuser", False)
        )
    )


def get_submission_queryset_for_user(user):
    queryset = Submission.objects.select_related(
        "school",
        "assignment",
        "assignment__teacher",
        "assignment__class_arm",
        "assignment__class_arm__class_level",
        "assignment__subject",
        "assignment__topic",
        "student",
    ).prefetch_related(
        "answers",
        "answers__assignment_question",
        "answers__selected_option",
    )

    if is_platform_admin(user):
        return queryset

    if not user or not user.is_authenticated:
        return queryset.none()

    if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
        return queryset.filter(school=user.school)

    if user.role == UserRole.TEACHER and user.school_id:
        return queryset.filter(school=user.school, assignment__teacher=user)

    if user.role == UserRole.STUDENT and user.school_id:
        return queryset.filter(school=user.school, student=user)

    return queryset.none()


def get_student_assignments(user):
    if not user or not user.is_authenticated or user.role != UserRole.STUDENT:
        return Assignment.objects.none()

    enrolled_class_arms = StudentEnrollment.objects.filter(
        school=user.school,
        student=user,
        is_active=True,
    ).values("class_arm_id")

    return (
        Assignment.objects.filter(
            school=user.school,
            class_arm_id__in=enrolled_class_arms,
            status=AssignmentStatus.PUBLISHED,
        )
        .select_related("class_arm", "class_arm__class_level", "subject", "topic")
        .prefetch_related(
            Prefetch(
                "submissions",
                queryset=Submission.objects.filter(student=user),
                to_attr="student_submissions",
            )
        )
        .order_by("due_at", "-created_at")
    )


def get_student_submission_for_assignment(student, assignment):
    return Submission.objects.filter(
        school=student.school,
        student=student,
        assignment=assignment,
    ).first()


def get_teacher_assignment_submissions(teacher, assignment):
    if (
        not teacher
        or not teacher.is_authenticated
        or teacher.role != UserRole.TEACHER
        or assignment.teacher_id != teacher.id
        or assignment.school_id != teacher.school_id
    ):
        return Submission.objects.none()

    return Submission.objects.filter(
        school=teacher.school,
        assignment=assignment,
    ).select_related("student", "assignment")


def get_submission_result_for_user(user, submission_id):
    queryset = get_submission_queryset_for_user(user)
    return get_object_or_404(queryset, pk=submission_id)
