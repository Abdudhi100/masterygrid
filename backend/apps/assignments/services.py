from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.academics.models import LessonLog, TeacherClassSubjectAssignment
from apps.common.choices import AssignmentStatus, QuestionStatus, UserRole
from apps.question_bank.models import Question


def validate_teacher_can_create_assignment(*, teacher, class_arm, subject, topic):
    if not teacher or not class_arm or not subject or not topic:
        raise ValidationError("Teacher, class arm, subject, and topic are required.")

    if teacher.role != UserRole.TEACHER:
        raise ValidationError({"teacher": "Assignment owner must have teacher role."})

    if not teacher.school_id:
        raise ValidationError({"teacher": "Teacher must belong to a school."})

    if class_arm.school_id != teacher.school_id:
        raise ValidationError({"class_arm": "Class arm must belong to teacher's school."})

    if subject.school_id and subject.school_id != teacher.school_id:
        raise ValidationError(
            {"subject": "Subject must be global or belong to teacher's school."}
        )

    if topic.subject_id != subject.id:
        raise ValidationError({"topic": "Topic must belong to the selected subject."})

    if topic.class_level_id != class_arm.class_level_id:
        raise ValidationError(
            {"topic": "Topic class level must match the selected class arm."}
        )

    if topic.school_id and topic.school_id != teacher.school_id:
        raise ValidationError(
            {"topic": "Topic must be global or belong to teacher's school."}
        )

    is_assigned = TeacherClassSubjectAssignment.objects.filter(
        school=teacher.school,
        teacher=teacher,
        class_arm=class_arm,
        subject=subject,
        is_active=True,
    ).exists()

    if not is_assigned:
        raise ValidationError(
            {
                "teacher": (
                    "Teacher must be assigned to this class arm and subject before "
                    "creating an assignment."
                )
            }
        )


def get_available_questions_for_assignment(
    *,
    school,
    subject,
    topic,
    class_level,
    question_count,
):
    queryset = Question.objects.filter(
        Q(school__isnull=True) | Q(school=school),
        subject=subject,
        topic=topic,
        class_level=class_level,
        status=QuestionStatus.APPROVED,
        is_active=True,
    ).select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
    ).prefetch_related("options", "media")

    available_count = queryset.count()
    if available_count < question_count:
        raise ValidationError(
            {
                "question_count": (
                    f"Only {available_count} approved question(s) are available for "
                    f"this topic; {question_count} requested."
                )
            }
        )

    return list(queryset.order_by("?")[:question_count])


@transaction.atomic
def create_assignment_from_topic(
    *,
    teacher,
    class_arm,
    subject,
    topic,
    title,
    question_count,
    instructions="",
    duration_minutes=None,
    starts_at=None,
    due_at=None,
    lesson_log=None,
):
    validate_teacher_can_create_assignment(
        teacher=teacher,
        class_arm=class_arm,
        subject=subject,
        topic=topic,
    )

    if lesson_log is not None:
        validate_lesson_log_matches_assignment(
            lesson_log=lesson_log,
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            topic=topic,
        )

    selected_questions = get_available_questions_for_assignment(
        school=teacher.school,
        subject=subject,
        topic=topic,
        class_level=class_arm.class_level,
        question_count=question_count,
    )

    from apps.assignments.models import Assignment, AssignmentQuestion

    assignment = Assignment(
        school=teacher.school,
        teacher=teacher,
        class_arm=class_arm,
        subject=subject,
        topic=topic,
        lesson_log=lesson_log,
        title=title,
        instructions=instructions,
        question_count=question_count,
        duration_minutes=duration_minutes,
        starts_at=starts_at,
        due_at=due_at,
        status=AssignmentStatus.DRAFT,
    )
    assignment.full_clean()
    assignment.save()

    for order, question in enumerate(selected_questions, start=1):
        assignment_question = AssignmentQuestion(
            assignment=assignment,
            question=question,
            order=order,
            marks=1,
        )
        assignment_question.full_clean()
        assignment_question.save()

    return assignment


def create_assignment_from_lesson_log(
    *,
    lesson_log,
    title,
    question_count,
    instructions="",
    duration_minutes=None,
    starts_at=None,
    due_at=None,
):
    if not isinstance(lesson_log, LessonLog):
        raise ValidationError({"lesson_log": "A valid lesson log is required."})

    return create_assignment_from_topic(
        teacher=lesson_log.teacher,
        class_arm=lesson_log.class_arm,
        subject=lesson_log.subject,
        topic=lesson_log.topic,
        lesson_log=lesson_log,
        title=title,
        instructions=instructions,
        question_count=question_count,
        duration_minutes=duration_minutes,
        starts_at=starts_at,
        due_at=due_at,
    )


def validate_lesson_log_matches_assignment(
    *,
    lesson_log,
    teacher,
    class_arm,
    subject,
    topic,
):
    if lesson_log.school_id != teacher.school_id:
        raise ValidationError({"lesson_log": "Lesson log must belong to teacher's school."})
    if lesson_log.teacher_id != teacher.id:
        raise ValidationError({"lesson_log": "Lesson log teacher must match assignment teacher."})
    if lesson_log.class_arm_id != class_arm.id:
        raise ValidationError(
            {"lesson_log": "Lesson log class arm must match assignment class arm."}
        )
    if lesson_log.subject_id != subject.id:
        raise ValidationError({"lesson_log": "Lesson log subject must match assignment subject."})
    if lesson_log.topic_id != topic.id:
        raise ValidationError({"lesson_log": "Lesson log topic must match assignment topic."})


def can_manage_assignment(assignment, user):
    if not user or not user.is_authenticated:
        return False

    if user.role == UserRole.PLATFORM_ADMIN or user.is_superuser:
        return True

    if user.role == UserRole.SCHOOL_ADMIN:
        return assignment.school_id == user.school_id

    if user.role == UserRole.TEACHER:
        return assignment.school_id == user.school_id and assignment.teacher_id == user.id

    return False


def publish_assignment(assignment, user):
    if not can_manage_assignment(assignment, user):
        raise PermissionDenied("You do not have permission to publish this assignment.")

    if assignment.status != AssignmentStatus.DRAFT:
        raise ValidationError({"status": "Only draft assignments can be published."})

    assignment_questions = list(assignment.assignment_questions.select_related("question"))
    if len(assignment_questions) != assignment.question_count:
        raise ValidationError(
            {
                "assignment_questions": (
                    "Assignment question count must match the configured question count."
                )
            }
        )

    for assignment_question in assignment_questions:
        assignment_question.full_clean()

    assignment.status = AssignmentStatus.PUBLISHED
    assignment.published_at = timezone.now()
    assignment.full_clean()
    assignment.save(update_fields=["status", "published_at", "updated_at"])
    from apps.notifications.services import notify_assignment_published

    notify_assignment_published(assignment, actor=user)
    return assignment


def close_assignment(assignment, user):
    if not can_manage_assignment(assignment, user):
        raise PermissionDenied("You do not have permission to close this assignment.")

    if assignment.status not in {AssignmentStatus.PUBLISHED, AssignmentStatus.DRAFT}:
        raise ValidationError(
            {"status": "Only draft or published assignments can be closed."}
        )

    assignment.status = AssignmentStatus.CLOSED
    assignment.full_clean()
    assignment.save(update_fields=["status", "updated_at"])
    return assignment


def archive_assignment(assignment, user):
    if not can_manage_assignment(assignment, user):
        raise PermissionDenied("You do not have permission to archive this assignment.")

    assignment.status = AssignmentStatus.ARCHIVED
    assignment.full_clean()
    assignment.save(update_fields=["status", "updated_at"])
    return assignment
