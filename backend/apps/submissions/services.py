import random
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.academics.models import StudentEnrollment
from apps.common.choices import AssignmentStatus, SubmissionStatus, UserRole
from apps.submissions.models import StudentAnswer, Submission


FINAL_SUBMISSION_STATUSES = {
    SubmissionStatus.SUBMITTED,
    SubmissionStatus.GRADED,
    SubmissionStatus.AUTO_SUBMITTED,
}


def validate_student_can_start_assignment(student, assignment):
    if not student or not student.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    if student.role != UserRole.STUDENT:
        raise ValidationError({"student": "Only students can start assignments."})

    if student.school_id != assignment.school_id:
        raise ValidationError({"assignment": "Assignment does not belong to your school."})

    if assignment.status != AssignmentStatus.PUBLISHED:
        raise ValidationError(
            {"assignment": "Only published assignments can be started."}
        )

    now = timezone.now()
    if assignment.starts_at and assignment.starts_at > now:
        raise ValidationError({"assignment": "This assignment has not started yet."})

    if assignment.due_at and assignment.due_at < now:
        raise ValidationError({"assignment": "This assignment is past its due date."})

    is_enrolled = StudentEnrollment.objects.filter(
        school=assignment.school,
        student=student,
        class_arm=assignment.class_arm,
        is_active=True,
    ).exists()
    if not is_enrolled:
        raise ValidationError(
            {"student": "You are not enrolled in this assignment's class arm."}
        )


@transaction.atomic
def create_or_get_submission(student, assignment):
    validate_student_can_start_assignment(student, assignment)

    submission, _created = Submission.objects.get_or_create(
        school=assignment.school,
        assignment=assignment,
        student=student,
        defaults={
            "status": SubmissionStatus.NOT_STARTED,
            "total_marks": get_assignment_total_marks(assignment),
        },
    )

    if submission.status in FINAL_SUBMISSION_STATUSES:
        raise ValidationError({"submission": "This assignment has already been submitted."})

    if not submission.question_order:
        submission.question_order = generate_question_order(assignment)

    if not submission.started_at:
        submission.started_at = timezone.now()

    submission.status = SubmissionStatus.IN_PROGRESS
    submission.total_marks = get_assignment_total_marks(assignment)
    submission.full_clean()
    submission.save(
        update_fields=[
            "status",
            "started_at",
            "question_order",
            "total_marks",
            "updated_at",
        ]
    )
    return submission


def generate_question_order(assignment):
    assignment_question_ids = list(
        assignment.assignment_questions.order_by("order").values_list("id", flat=True)
    )
    random.shuffle(assignment_question_ids)
    return assignment_question_ids


def get_submission_questions_for_student(submission):
    ordered_ids = submission.question_order or generate_question_order(submission.assignment)
    assignment_questions = submission.assignment.assignment_questions.select_related(
        "question",
    ).prefetch_related(
        "question__options",
        "question__media",
    )
    by_id = {item.id: item for item in assignment_questions}
    return [by_id[item_id] for item_id in ordered_ids if item_id in by_id]


@transaction.atomic
def save_submission_answers(submission, answers):
    if submission.status != SubmissionStatus.IN_PROGRESS:
        raise ValidationError(
            {"submission": "Answers can only be saved for in-progress submissions."}
        )

    expected_ids = set(submission.question_order)
    submitted_ids = {answer["assignment_question"].id for answer in answers}
    if len(submitted_ids) != len(answers):
        raise ValidationError(
            {"answers": "Duplicate answers for the same assignment question are not allowed."}
        )

    if submitted_ids != expected_ids:
        raise ValidationError(
            {"answers": "Every assignment question must have exactly one answer."}
        )

    saved_answers = []
    now = timezone.now()
    for answer in answers:
        assignment_question = answer["assignment_question"]
        selected_option = answer["selected_option"]

        if assignment_question.assignment_id != submission.assignment_id:
            raise ValidationError(
                {
                    "assignment_question": (
                        "Assignment question does not belong to this submission."
                    )
                }
            )

        if selected_option.question_id != assignment_question.question_id:
            raise ValidationError(
                {"selected_option": "Selected option does not belong to this question."}
            )

        student_answer, _created = StudentAnswer.objects.update_or_create(
            submission=submission,
            assignment_question=assignment_question,
            defaults={
                "selected_option": selected_option,
                "answered_at": now,
            },
        )
        saved_answers.append(student_answer)

    return saved_answers


@transaction.atomic
def grade_submission(submission):
    answers = list(
        submission.answers.select_related(
            "selected_option",
            "assignment_question",
            "assignment_question__question",
        )
    )
    expected_count = len(submission.question_order)
    if len(answers) != expected_count:
        raise ValidationError({"answers": "Submission is missing answers."})

    score = 0
    total_marks = get_assignment_total_marks(submission.assignment)

    for answer in answers:
        is_correct = bool(answer.selected_option and answer.selected_option.is_correct)
        marks_awarded = answer.assignment_question.marks if is_correct else 0
        answer.is_correct = is_correct
        answer.marks_awarded = marks_awarded
        answer.full_clean()
        answer.save(update_fields=["is_correct", "marks_awarded", "updated_at"])
        score += marks_awarded

    percentage = Decimal("0.00")
    if total_marks:
        percentage = (
            Decimal(score) / Decimal(total_marks) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    now = timezone.now()
    submission.score = score
    submission.total_marks = total_marks
    submission.percentage = percentage
    submission.submitted_at = submission.submitted_at or now
    submission.graded_at = now
    submission.status = SubmissionStatus.GRADED
    submission.full_clean()
    submission.save(
        update_fields=[
            "score",
            "total_marks",
            "percentage",
            "submitted_at",
            "graded_at",
            "status",
            "updated_at",
        ]
    )
    return submission


@transaction.atomic
def submit_assignment(submission, answers):
    if submission.status in FINAL_SUBMISSION_STATUSES:
        raise ValidationError({"submission": "This assignment has already been submitted."})

    if submission.status != SubmissionStatus.IN_PROGRESS:
        raise ValidationError({"submission": "Submission must be in progress."})

    if submission.assignment.status != AssignmentStatus.PUBLISHED:
        raise ValidationError({"assignment": "Assignment is no longer accepting submissions."})

    now = timezone.now()
    if submission.assignment.due_at and submission.assignment.due_at < now:
        raise ValidationError({"assignment": "This assignment is past its due date."})

    save_submission_answers(submission, answers)

    submission.submitted_at = now
    if submission.started_at:
        elapsed_seconds = int((now - submission.started_at).total_seconds())
        submission.time_spent_seconds = max(1, elapsed_seconds)
    submission.status = SubmissionStatus.SUBMITTED
    submission.save(
        update_fields=[
            "submitted_at",
            "time_spent_seconds",
            "status",
            "updated_at",
        ]
    )
    return grade_submission(submission)


def get_assignment_total_marks(assignment):
    return sum(
        assignment.assignment_questions.values_list("marks", flat=True)
    )


def validate_submission_result_access(user, submission):
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    if user.role == UserRole.PLATFORM_ADMIN or user.is_superuser:
        return

    if user.role == UserRole.SCHOOL_ADMIN and submission.school_id == user.school_id:
        return

    if (
        user.role == UserRole.TEACHER
        and submission.school_id == user.school_id
        and submission.assignment.teacher_id == user.id
    ):
        return

    if user.role == UserRole.STUDENT and submission.student_id == user.id:
        return

    raise PermissionDenied("You do not have access to this submission.")
