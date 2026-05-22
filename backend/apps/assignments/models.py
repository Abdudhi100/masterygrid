from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.choices import AssignmentStatus, QuestionStatus, UserRole
from apps.common.models import TimeStampedModel


class Assignment(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="assignments",
        on_delete=models.CASCADE,
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assignments",
        on_delete=models.CASCADE,
    )
    class_arm = models.ForeignKey(
        "academics.ClassArm",
        related_name="assignments",
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        "academics.Subject",
        related_name="assignments",
        on_delete=models.PROTECT,
    )
    topic = models.ForeignKey(
        "academics.Topic",
        related_name="assignments",
        on_delete=models.PROTECT,
    )
    lesson_log = models.ForeignKey(
        "academics.LessonLog",
        related_name="assignments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    question_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "teacher", "status"]),
            models.Index(fields=["school", "class_arm", "subject", "topic"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if self.title is not None and not self.title.strip():
            raise ValidationError({"title": "Assignment title cannot be blank."})

        if self.starts_at and self.due_at and self.starts_at > self.due_at:
            raise ValidationError({"due_at": "Due date must be after start date."})

        required_relations = [
            self.school_id,
            self.teacher_id,
            self.class_arm_id,
            self.subject_id,
            self.topic_id,
        ]
        if not all(required_relations):
            return

        if self.teacher.role != UserRole.TEACHER:
            raise ValidationError({"teacher": "Assignment owner must have teacher role."})

        if self.teacher.school_id != self.school_id:
            raise ValidationError(
                {"teacher": "Teacher must belong to the assignment school."}
            )

        if self.class_arm.school_id != self.school_id:
            raise ValidationError(
                {"class_arm": "Class arm must belong to the assignment school."}
            )

        if self.subject.school_id and self.subject.school_id != self.school_id:
            raise ValidationError(
                {"subject": "Subject must be global or belong to the assignment school."}
            )

        if self.topic.subject_id != self.subject_id:
            raise ValidationError({"topic": "Topic must belong to the selected subject."})

        if self.topic.class_level_id != self.class_arm.class_level_id:
            raise ValidationError(
                {"topic": "Topic class level must match the selected class arm."}
            )

        if self.topic.school_id and self.topic.school_id != self.school_id:
            raise ValidationError(
                {"topic": "Topic must be global or belong to the assignment school."}
            )

        if self.lesson_log_id:
            if self.lesson_log.school_id != self.school_id:
                raise ValidationError(
                    {"lesson_log": "Lesson log must belong to the assignment school."}
                )
            if self.lesson_log.teacher_id != self.teacher_id:
                raise ValidationError(
                    {"lesson_log": "Lesson log teacher must match assignment teacher."}
                )
            if self.lesson_log.class_arm_id != self.class_arm_id:
                raise ValidationError(
                    {"lesson_log": "Lesson log class arm must match assignment class arm."}
                )
            if self.lesson_log.subject_id != self.subject_id:
                raise ValidationError(
                    {"lesson_log": "Lesson log subject must match assignment subject."}
                )
            if self.lesson_log.topic_id != self.topic_id:
                raise ValidationError(
                    {"lesson_log": "Lesson log topic must match assignment topic."}
                )

        from apps.assignments.services import validate_teacher_can_create_assignment

        validate_teacher_can_create_assignment(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
        )


class AssignmentQuestion(TimeStampedModel):
    assignment = models.ForeignKey(
        Assignment,
        related_name="assignment_questions",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        "question_bank.Question",
        related_name="assignment_questions",
        on_delete=models.PROTECT,
    )
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    marks = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "order"],
                name="unique_assignment_question_order",
            ),
            models.UniqueConstraint(
                fields=["assignment", "question"],
                name="unique_question_per_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.assignment_id} - Q{self.order}"

    def clean(self):
        super().clean()

        if not self.assignment_id or not self.question_id:
            return

        if (
            self.question.status != QuestionStatus.APPROVED
            or not self.question.is_active
        ):
            raise ValidationError(
                {"question": "Only approved and active questions can be assigned."}
            )

        if self.question.subject_id != self.assignment.subject_id:
            raise ValidationError(
                {"question": "Question subject must match the assignment subject."}
            )

        if self.question.topic_id != self.assignment.topic_id:
            raise ValidationError(
                {"question": "Question topic must match the assignment topic."}
            )

        if self.question.class_level_id != self.assignment.class_arm.class_level_id:
            raise ValidationError(
                {"question": "Question class level must match the assignment class level."}
            )

        if (
            self.question.school_id is not None
            and self.question.school_id != self.assignment.school_id
        ):
            raise ValidationError(
                {
                    "question": (
                        "Question must be global or belong to the assignment school."
                    )
                }
            )
