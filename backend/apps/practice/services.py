from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.academics.models import StudentEnrollment
from apps.common.choices import UserRole
from apps.practice.models import (
    PracticeAnswer,
    PracticeDifficulty,
    PracticeSession,
    PracticeSessionQuestion,
    PracticeSessionStatus,
)
from apps.practice.selectors import get_available_practice_questions


def _resolve_student_enrollment(student, class_level=None):
    queryset = StudentEnrollment.objects.filter(
        school=student.school,
        student=student,
        is_active=True,
    ).select_related("class_arm", "class_arm__class_level")

    if class_level is not None:
        queryset = queryset.filter(class_arm__class_level=class_level)

    return queryset.order_by("-created_at").first()


def _validate_practice_request(student, subject, topic, class_level, class_arm, count):
    if not student or not student.is_authenticated:
        raise ValidationError({"student": "Authentication is required."})

    if student.role != UserRole.STUDENT:
        raise ValidationError({"student": "Only students can start practice sessions."})

    if not student.school_id:
        raise ValidationError({"student": "Student must belong to a school."})

    if count <= 0:
        raise ValidationError({"question_count": "Question count must be positive."})

    if subject.school_id and subject.school_id != student.school_id:
        raise ValidationError(
            {"subject": "Subject must be global or belong to your school."}
        )

    if topic is not None:
        if topic.subject_id != subject.id:
            raise ValidationError({"topic": "Topic must belong to the subject."})
        if topic.school_id and topic.school_id != student.school_id:
            raise ValidationError(
                {"topic": "Topic must be global or belong to your school."}
            )

    if class_level is not None and class_level.school_id != student.school_id:
        raise ValidationError({"class_level": "Class level must belong to your school."})

    if class_arm is not None:
        if class_arm.school_id != student.school_id:
            raise ValidationError({"class_arm": "Class arm must belong to your school."})
        if class_level is not None and class_arm.class_level_id != class_level.id:
            raise ValidationError(
                {"class_arm": "Class arm must belong to the selected class level."}
            )

    if topic is not None and class_level is not None and topic.class_level_id != class_level.id:
        raise ValidationError(
            {"topic": "Topic must belong to the selected class level."}
        )


def _snapshot_options(question):
    return [
        {
            "id": option.id,
            "label": option.label,
            "text": option.text,
            "is_correct": option.is_correct,
        }
        for option in question.options.order_by("label")
    ]


@transaction.atomic
def start_practice_session(
    student,
    subject,
    topic=None,
    class_level=None,
    difficulty=PracticeDifficulty.MIXED,
    question_count=10,
):
    if topic is not None and class_level is None:
        class_level = topic.class_level

    enrollment = _resolve_student_enrollment(student, class_level=class_level)
    class_arm = enrollment.class_arm if enrollment else None
    if class_level is None and enrollment:
        class_level = enrollment.class_arm.class_level

    _validate_practice_request(
        student=student,
        subject=subject,
        topic=topic,
        class_level=class_level,
        class_arm=class_arm,
        count=question_count,
    )

    questions = get_available_practice_questions(
        student=student,
        subject=subject,
        topic=topic,
        class_level=class_level,
        difficulty=difficulty,
        count=question_count,
    )

    session = PracticeSession(
        school=student.school,
        student=student,
        subject=subject,
        topic=topic,
        class_level=class_level,
        class_arm=class_arm,
        difficulty=difficulty,
        question_count_requested=question_count,
        status=PracticeSessionStatus.IN_PROGRESS,
        started_at=timezone.now(),
    )
    session.full_clean()
    session.save()

    total_marks = 0
    for index, question in enumerate(questions, start=1):
        session_question = PracticeSessionQuestion(
            session=session,
            question=question,
            order=index,
            marks=1,
            question_text=question.question_text,
            explanation=question.explanation,
            options_snapshot=_snapshot_options(question),
        )
        session_question.full_clean()
        session_question.save()
        total_marks += session_question.marks

    session.total_marks = total_marks
    session.full_clean()
    session.save(update_fields=["total_marks", "updated_at"])
    return session


@transaction.atomic
def submit_practice_session(session, answers):
    if session.status != PracticeSessionStatus.IN_PROGRESS:
        raise ValidationError({"session": "This practice session has already been submitted."})

    expected_ids = set(session.session_questions.values_list("id", flat=True))
    submitted_ids = {answer["session_question"].id for answer in answers}

    if len(submitted_ids) != len(answers):
        raise ValidationError(
            {"answers": "Duplicate answers for the same practice question are not allowed."}
        )

    if submitted_ids != expected_ids:
        raise ValidationError(
            {"answers": "Every practice question must have exactly one answer."}
        )

    now = timezone.now()
    for answer in answers:
        session_question = answer["session_question"]
        selected_option = answer["selected_option"]

        if session_question.session_id != session.id:
            raise ValidationError(
                {"session_question": "Practice question does not belong to this session."}
            )

        if selected_option.question_id != session_question.question_id:
            raise ValidationError(
                {"selected_option": "Selected option does not belong to this question."}
            )

        practice_answer, _created = PracticeAnswer.objects.update_or_create(
            session=session,
            session_question=session_question,
            defaults={
                "selected_option": selected_option,
                "selected_label": selected_option.label,
                "answered_at": now,
            },
        )
        practice_answer.full_clean()
        practice_answer.save()

    session.submitted_at = now
    session.status = PracticeSessionStatus.SUBMITTED
    session.save(update_fields=["submitted_at", "status", "updated_at"])
    return grade_practice_session(session)


@transaction.atomic
def grade_practice_session(session):
    answers = list(
        session.answers.select_related(
            "selected_option",
            "session_question",
            "session_question__question",
        )
    )
    expected_count = session.session_questions.count()
    if len(answers) != expected_count:
        raise ValidationError({"answers": "Practice session is missing answers."})

    score = 0
    total_marks = sum(
        session.session_questions.values_list("marks", flat=True)
    )

    for answer in answers:
        is_correct = bool(answer.selected_option and answer.selected_option.is_correct)
        marks_awarded = answer.session_question.marks if is_correct else 0
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

    session.score = score
    session.total_marks = total_marks
    session.percentage = percentage
    session.status = PracticeSessionStatus.SUBMITTED
    session.submitted_at = session.submitted_at or timezone.now()
    session.full_clean()
    session.save(
        update_fields=[
            "score",
            "total_marks",
            "percentage",
            "status",
            "submitted_at",
            "updated_at",
        ]
    )
    return session


def get_practice_result(session):
    if session.status != PracticeSessionStatus.SUBMITTED:
        raise ValidationError(
            {"session": "Practice results are available only after submission."}
        )
    return session
