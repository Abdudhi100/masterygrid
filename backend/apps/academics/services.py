from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.academics.models import AcademicSession, TeacherClassSubjectAssignment, Term
from apps.common.choices import UserRole


def get_active_academic_session(school):
    return (
        AcademicSession.objects.filter(school=school, is_active=True)
        .order_by("-starts_at")
        .first()
    )


def get_active_term(school):
    return (
        Term.objects.filter(school=school, is_active=True)
        .select_related("academic_session")
        .order_by("-starts_at")
        .first()
    )


def get_teacher_assignments(user):
    if not user or not user.is_authenticated or user.role != UserRole.TEACHER:
        return TeacherClassSubjectAssignment.objects.none()

    return TeacherClassSubjectAssignment.objects.filter(
        teacher=user,
        school=user.school,
        is_active=True,
    ).select_related(
        "school",
        "teacher",
        "class_arm",
        "class_arm__class_level",
        "subject",
        "academic_session",
        "term",
    )


def validate_teacher_can_log_lesson(
    *,
    user,
    class_arm,
    subject,
    topic,
    academic_session=None,
    term=None,
    school=None,
):
    if not user or not class_arm or not subject or not topic:
        raise ValidationError("Teacher, class arm, subject, and topic are required.")

    if user.role != UserRole.TEACHER:
        raise ValidationError({"teacher": "Lesson logs can only be created for teachers."})

    if school and user.school_id != school.id:
        raise ValidationError({"teacher": "Teacher must belong to the selected school."})

    effective_school = school or user.school
    if effective_school is None:
        raise ValidationError({"school": "A teacher lesson log must belong to a school."})

    if class_arm.school_id != effective_school.id:
        raise ValidationError({"class_arm": "Class arm must belong to the selected school."})

    if subject.school_id and subject.school_id != effective_school.id:
        raise ValidationError(
            {"subject": "Subject must be global or belong to the selected school."}
        )

    if topic.subject_id != subject.id:
        raise ValidationError({"topic": "Topic must belong to the selected subject."})

    if topic.class_level_id != class_arm.class_level_id:
        raise ValidationError(
            {"topic": "Topic class level must match the selected class arm."}
        )

    if topic.school_id and topic.school_id != effective_school.id:
        raise ValidationError(
            {"topic": "Topic must be global or belong to the selected school."}
        )

    if academic_session and academic_session.school_id != effective_school.id:
        raise ValidationError(
            {"academic_session": "Academic session must belong to the selected school."}
        )

    if term:
        if term.school_id != effective_school.id:
            raise ValidationError({"term": "Term must belong to the selected school."})
        if academic_session and term.academic_session_id != academic_session.id:
            raise ValidationError(
                {"term": "Term must belong to the selected academic session."}
            )

    assignment_filters = Q(academic_session__isnull=True)
    if academic_session:
        assignment_filters |= Q(academic_session=academic_session)

    term_filters = Q(term__isnull=True)
    if term:
        term_filters |= Q(term=term)

    is_assigned = TeacherClassSubjectAssignment.objects.filter(
        assignment_filters,
        term_filters,
        school=effective_school,
        teacher=user,
        class_arm=class_arm,
        subject=subject,
        is_active=True,
    ).exists()

    if not is_assigned:
        raise ValidationError(
            {
                "teacher": (
                    "Teacher must be assigned to this class arm and subject before "
                    "logging a lesson."
                )
            }
        )
