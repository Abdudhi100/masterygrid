from django.db.models import Q

from apps.accounts.models import User
from apps.academics.models import StudentEnrollment, TeacherClassSubjectAssignment
from apps.common.choices import UserRole
from apps.interventions.models import StudentIntervention
from apps.submissions.models import Submission


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (user.role == UserRole.PLATFORM_ADMIN or getattr(user, "is_superuser", False))
    )


def get_students_accessible_to_teacher(teacher):
    if not teacher or teacher.role != UserRole.TEACHER or not teacher.school_id:
        return User.objects.none().values_list("id", flat=True)

    class_arm_ids = TeacherClassSubjectAssignment.objects.filter(
        school=teacher.school,
        teacher=teacher,
        is_active=True,
    ).values_list("class_arm_id", flat=True)

    taught_student_ids = StudentEnrollment.objects.filter(
        school=teacher.school,
        class_arm_id__in=class_arm_ids,
        is_active=True,
    ).order_by().values_list("student_id", flat=True)

    submitted_student_ids = Submission.objects.filter(
        school=teacher.school,
        assignment__teacher=teacher,
    ).order_by().values_list("student_id", flat=True)

    return taught_student_ids.union(submitted_student_ids)


def teacher_can_access_student(teacher, student):
    if not teacher or not student:
        return False
    if teacher.role != UserRole.TEACHER or not teacher.school_id:
        return False
    if student.school_id != teacher.school_id:
        return False

    class_arm_ids = TeacherClassSubjectAssignment.objects.filter(
        school=teacher.school,
        teacher=teacher,
        is_active=True,
    ).values("class_arm_id")

    teaches_student_class = StudentEnrollment.objects.filter(
        school=teacher.school,
        student=student,
        is_active=True,
        class_arm_id__in=class_arm_ids,
    ).exists()
    if teaches_student_class:
        return True

    return Submission.objects.filter(
        school=teacher.school,
        student=student,
        assignment__teacher=teacher,
    ).exists()


def user_can_access_student(user, student):
    if not user or not user.is_authenticated or not student:
        return False

    if is_platform_admin(user):
        return True

    if user.role == UserRole.SCHOOL_ADMIN:
        return bool(user.school_id and student.school_id == user.school_id)

    if user.role == UserRole.TEACHER:
        return teacher_can_access_student(user, student)

    return False


def get_interventions_for_user(user):
    queryset = StudentIntervention.objects.select_related(
        "school",
        "student",
        "student__student_profile",
        "created_by",
        "assigned_to",
        "source_assignment",
        "source_subject",
        "source_topic",
        "source_class_arm",
        "source_class_arm__class_level",
    ).prefetch_related("notes")

    if not user or not user.is_authenticated:
        return queryset.none()

    if is_platform_admin(user):
        return queryset

    if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
        return queryset.filter(school=user.school)

    if user.role == UserRole.TEACHER and user.school_id:
        accessible_student_ids = get_students_accessible_to_teacher(user)
        return queryset.filter(
            school=user.school,
        ).filter(
            Q(student_id__in=accessible_student_ids)
            | Q(created_by=user)
            | Q(assigned_to=user)
        )

    return queryset.none()
