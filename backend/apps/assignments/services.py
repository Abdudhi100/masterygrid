from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.academics.models import LessonLog, TeacherClassSubjectAssignment
from apps.common.choices import AssignmentStatus, QuestionStatus, SubmissionStatus, UserRole
from apps.question_bank.models import Question


DUE_SOON_WINDOW = timedelta(hours=24)


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
    allow_late_submissions=False,
    late_submission_deadline=None,
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
        allow_late_submissions=allow_late_submissions,
        late_submission_deadline=late_submission_deadline,
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
    allow_late_submissions=False,
    late_submission_deadline=None,
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
        allow_late_submissions=allow_late_submissions,
        late_submission_deadline=late_submission_deadline,
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


def is_assignment_overdue(assignment, now=None):
    now = now or timezone.now()
    return bool(assignment.due_at and assignment.due_at < now)


def is_late_submission_window_open(assignment, now=None):
    now = now or timezone.now()
    if not assignment.allow_late_submissions:
        return False
    if not assignment.due_at or assignment.due_at >= now:
        return False
    if assignment.late_submission_deadline:
        return now <= assignment.late_submission_deadline
    return True


def is_assignment_open_for_student(assignment, now=None):
    now = now or timezone.now()
    if assignment.status != AssignmentStatus.PUBLISHED:
        return False
    if assignment.starts_at and assignment.starts_at > now:
        return False
    if assignment.due_at and assignment.due_at < now:
        return is_late_submission_window_open(assignment, now=now)
    return True


def get_assignment_availability(assignment, now=None):
    now = now or timezone.now()
    status = get_deadline_status(assignment, now=now)
    return {
        "deadline_status": status,
        "is_overdue": is_assignment_overdue(assignment, now=now),
        "is_due_soon": (
            assignment.status == AssignmentStatus.PUBLISHED
            and bool(assignment.due_at)
            and now <= assignment.due_at <= now + DUE_SOON_WINDOW
        ),
        "can_submit_now": is_assignment_open_for_student(assignment, now=now),
    }


def get_deadline_status(assignment, submission=None, now=None):
    now = now or timezone.now()
    if submission is not None:
        if submission.status in {SubmissionStatus.GRADED, SubmissionStatus.AUTO_SUBMITTED}:
            return "graded"
        if submission.status == SubmissionStatus.SUBMITTED:
            return "submitted"

    if assignment.status == AssignmentStatus.DRAFT:
        return "draft"
    if assignment.status in {AssignmentStatus.CLOSED, AssignmentStatus.ARCHIVED}:
        return "closed"
    if assignment.starts_at and assignment.starts_at > now:
        return "scheduled"
    if assignment.due_at and assignment.due_at < now:
        return "late_open" if is_late_submission_window_open(assignment, now=now) else "overdue"
    if assignment.due_at and assignment.due_at <= now + DUE_SOON_WINDOW:
        return "due_soon"
    return "open"


def _validate_deadline_payload(*, due_at, allow_late_submissions, late_submission_deadline):
    now = timezone.now()
    if due_at is None:
        raise ValidationError({"due_at": "Due date is required."})
    if due_at <= now:
        raise ValidationError({"due_at": "Due date must be in the future."})
    if late_submission_deadline:
        if not allow_late_submissions:
            raise ValidationError(
                {
                    "late_submission_deadline": (
                        "Enable late submissions before setting a late deadline."
                    )
                }
            )
        if late_submission_deadline <= due_at:
            raise ValidationError(
                {
                    "late_submission_deadline": (
                        "Late submission deadline must be after the due date."
                    )
                }
            )


def _preserve_original_due_at(assignment, new_due_at):
    if (
        assignment.due_at
        and new_due_at
        and assignment.due_at != new_due_at
        and assignment.original_due_at is None
    ):
        assignment.original_due_at = assignment.due_at


def extend_assignment_deadline(
    *,
    assignment,
    user,
    due_at,
    allow_late_submissions=None,
    late_submission_deadline=None,
):
    if not can_manage_assignment(assignment, user):
        raise PermissionDenied("You do not have permission to extend this assignment.")

    if assignment.status == AssignmentStatus.ARCHIVED:
        raise ValidationError({"status": "Archived assignments cannot be extended."})

    effective_allow_late = (
        assignment.allow_late_submissions
        if allow_late_submissions is None
        else allow_late_submissions
    )
    _validate_deadline_payload(
        due_at=due_at,
        allow_late_submissions=effective_allow_late,
        late_submission_deadline=late_submission_deadline,
    )

    _preserve_original_due_at(assignment, due_at)
    assignment.due_at = due_at
    assignment.allow_late_submissions = effective_allow_late
    assignment.late_submission_deadline = (
        late_submission_deadline if effective_allow_late else None
    )
    assignment.deadline_extended_at = timezone.now()
    assignment.deadline_extended_by = user
    assignment.full_clean()
    assignment.save(
        update_fields=[
            "due_at",
            "original_due_at",
            "allow_late_submissions",
            "late_submission_deadline",
            "deadline_extended_at",
            "deadline_extended_by",
            "updated_at",
        ]
    )

    from apps.notifications.services import notify_assignment_deadline_extended

    notify_assignment_deadline_extended(assignment, actor=user)
    return assignment


def reopen_assignment(
    *,
    assignment,
    user,
    due_at=None,
    allow_late_submissions=None,
    late_submission_deadline=None,
):
    if not can_manage_assignment(assignment, user):
        raise PermissionDenied("You do not have permission to reopen this assignment.")

    if assignment.status == AssignmentStatus.ARCHIVED:
        raise ValidationError({"status": "Archived assignments cannot be reopened."})

    if assignment.status not in {AssignmentStatus.CLOSED, AssignmentStatus.PUBLISHED}:
        raise ValidationError({"status": "Only closed or published assignments can be reopened."})

    effective_due_at = due_at or assignment.due_at
    effective_allow_late = (
        assignment.allow_late_submissions
        if allow_late_submissions is None
        else allow_late_submissions
    )
    if effective_due_at and effective_due_at <= timezone.now():
        raise ValidationError({"due_at": "Reopened assignments must have a future due date."})
    if late_submission_deadline:
        if not effective_allow_late:
            raise ValidationError(
                {
                    "late_submission_deadline": (
                        "Enable late submissions before setting a late deadline."
                    )
                }
            )
        if effective_due_at and late_submission_deadline <= effective_due_at:
            raise ValidationError(
                {
                    "late_submission_deadline": (
                        "Late submission deadline must be after the due date."
                    )
                }
            )

    _preserve_original_due_at(assignment, effective_due_at)
    assignment.status = AssignmentStatus.PUBLISHED
    assignment.due_at = effective_due_at
    assignment.allow_late_submissions = effective_allow_late
    assignment.late_submission_deadline = (
        late_submission_deadline if effective_allow_late else None
    )
    assignment.deadline_extended_at = timezone.now()
    assignment.deadline_extended_by = user
    assignment.full_clean()
    assignment.save(
        update_fields=[
            "status",
            "due_at",
            "original_due_at",
            "allow_late_submissions",
            "late_submission_deadline",
            "deadline_extended_at",
            "deadline_extended_by",
            "updated_at",
        ]
    )

    from apps.notifications.services import notify_assignment_reopened

    notify_assignment_reopened(assignment, actor=user)
    return assignment


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
