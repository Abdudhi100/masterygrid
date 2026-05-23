from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.choices import QuestionStatus, UserRole
from apps.common.models import TimeStampedModel
from apps.question_bank.models import QuestionDifficulty, QuestionOptionLabel


class PracticeDifficulty(models.TextChoices):
    EASY = QuestionDifficulty.EASY, "Easy"
    MEDIUM = QuestionDifficulty.MEDIUM, "Medium"
    HARD = QuestionDifficulty.HARD, "Hard"
    MIXED = "mixed", "Mixed"


class PracticeSessionStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In Progress"
    SUBMITTED = "submitted", "Submitted"
    ABANDONED = "abandoned", "Abandoned"


class PracticeSession(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="practice_sessions",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="practice_sessions",
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        "academics.Subject",
        related_name="practice_sessions",
        on_delete=models.PROTECT,
    )
    topic = models.ForeignKey(
        "academics.Topic",
        related_name="practice_sessions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    class_level = models.ForeignKey(
        "academics.ClassLevel",
        related_name="practice_sessions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    class_arm = models.ForeignKey(
        "academics.ClassArm",
        related_name="practice_sessions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    difficulty = models.CharField(
        max_length=16,
        choices=PracticeDifficulty.choices,
        default=PracticeDifficulty.MIXED,
    )
    question_count_requested = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=PracticeSessionStatus.choices,
        default=PracticeSessionStatus.IN_PROGRESS,
    )
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at", "-created_at"]
        indexes = [
            models.Index(fields=["school", "student", "status"]),
            models.Index(fields=["school", "subject", "topic"]),
            models.Index(fields=["student", "started_at"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} practice"

    def clean(self):
        super().clean()

        if self.question_count_requested is not None and self.question_count_requested <= 0:
            raise ValidationError(
                {"question_count_requested": "Question count must be positive."}
            )

        if not self.school_id or not self.student_id:
            return

        if self.student.role != UserRole.STUDENT:
            raise ValidationError({"student": "Practice owner must have student role."})

        if self.student.school_id != self.school_id:
            raise ValidationError(
                {"student": "Student must belong to the practice session school."}
            )

        if self.class_level_id and self.class_level.school_id != self.school_id:
            raise ValidationError(
                {"class_level": "Class level must belong to the student's school."}
            )

        if self.class_arm_id:
            if self.class_arm.school_id != self.school_id:
                raise ValidationError(
                    {"class_arm": "Class arm must belong to the student's school."}
                )
            if self.class_level_id and self.class_arm.class_level_id != self.class_level_id:
                raise ValidationError(
                    {"class_arm": "Class arm must belong to the selected class level."}
                )

        if self.subject_id and self.subject.school_id and self.subject.school_id != self.school_id:
            raise ValidationError(
                {"subject": "Subject must be global or belong to the student's school."}
            )

        if self.topic_id:
            if self.topic.subject_id != self.subject_id:
                raise ValidationError(
                    {"topic": "Topic must belong to the selected subject."}
                )
            if self.class_level_id and self.topic.class_level_id != self.class_level_id:
                raise ValidationError(
                    {"topic": "Topic must belong to the selected class level."}
                )
            if self.topic.school_id and self.topic.school_id != self.school_id:
                raise ValidationError(
                    {"topic": "Topic must be global or belong to the student's school."}
                )

        if self.percentage is not None and not Decimal("0.00") <= self.percentage <= Decimal("100.00"):
            raise ValidationError(
                {"percentage": "Percentage must be between 0 and 100."}
            )


class PracticeSessionQuestion(TimeStampedModel):
    session = models.ForeignKey(
        PracticeSession,
        related_name="session_questions",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        "question_bank.Question",
        related_name="practice_session_questions",
        on_delete=models.PROTECT,
    )
    order = models.PositiveIntegerField()
    marks = models.PositiveIntegerField(default=1)
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    options_snapshot = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "question"],
                name="unique_practice_question_per_session",
            ),
            models.UniqueConstraint(
                fields=["session", "order"],
                name="unique_practice_question_order_per_session",
            ),
        ]
        indexes = [
            models.Index(fields=["session", "order"]),
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"{self.session_id} - question {self.order}"

    def clean(self):
        super().clean()

        if self.order is not None and self.order <= 0:
            raise ValidationError({"order": "Question order must be positive."})

        if self.marks is not None and self.marks <= 0:
            raise ValidationError({"marks": "Marks must be positive."})

        if not self.session_id or not self.question_id:
            return

        if (
            self.question.status != QuestionStatus.APPROVED
            or not self.question.is_active
        ):
            raise ValidationError(
                {"question": "Practice questions must be approved and active."}
            )

        if not (
            self.question.school_id is None
            or self.question.school_id == self.session.school_id
        ):
            raise ValidationError(
                {"question": "Question must be global or belong to the session school."}
            )

        if self.question.subject_id != self.session.subject_id:
            raise ValidationError(
                {"question": "Question subject must match the practice session."}
            )

        if self.session.topic_id and self.question.topic_id != self.session.topic_id:
            raise ValidationError(
                {"question": "Question topic must match the practice session."}
            )

        if (
            self.session.class_level_id
            and self.question.class_level_id != self.session.class_level_id
        ):
            raise ValidationError(
                {"question": "Question class level must match the practice session."}
            )

        if (
            self.session.difficulty != PracticeDifficulty.MIXED
            and self.question.difficulty != self.session.difficulty
        ):
            raise ValidationError(
                {"question": "Question difficulty must match the practice session."}
            )


class PracticeAnswer(TimeStampedModel):
    session = models.ForeignKey(
        PracticeSession,
        related_name="answers",
        on_delete=models.CASCADE,
    )
    session_question = models.ForeignKey(
        PracticeSessionQuestion,
        related_name="answers",
        on_delete=models.CASCADE,
    )
    selected_option = models.ForeignKey(
        "question_bank.QuestionOption",
        related_name="practice_answers",
        on_delete=models.PROTECT,
    )
    selected_label = models.CharField(
        max_length=1,
        choices=QuestionOptionLabel.choices,
        blank=True,
    )
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["session_question__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "session_question"],
                name="unique_practice_answer_per_session_question",
            )
        ]
        indexes = [
            models.Index(fields=["session", "session_question"]),
        ]

    def __str__(self):
        return f"{self.session_id} - {self.session_question_id}"

    def clean(self):
        super().clean()

        if not self.session_id or not self.session_question_id:
            return

        if self.session_question.session_id != self.session_id:
            raise ValidationError(
                {
                    "session_question": (
                        "Practice question must belong to the selected session."
                    )
                }
            )

        if (
            self.selected_option_id
            and self.selected_option.question_id != self.session_question.question_id
        ):
            raise ValidationError(
                {"selected_option": "Selected option must belong to this question."}
            )
