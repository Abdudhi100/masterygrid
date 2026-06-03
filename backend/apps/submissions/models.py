from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.academics.models import StudentEnrollment
from apps.common.choices import UserRole
from apps.common.choices import SubmissionStatus
from apps.common.models import TimeStampedModel


class Submission(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="submissions",
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        "assignments.Assignment",
        related_name="submissions",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="submissions",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=16,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.NOT_STARTED,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    time_spent_seconds = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )
    is_late = models.BooleanField(default=False)
    submitted_after_due_seconds = models.PositiveIntegerField(null=True, blank=True)
    deadline_status_at_submit = models.CharField(max_length=32, blank=True)
    question_order = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="unique_submission_per_assignment_student",
            )
        ]
        indexes = [
            models.Index(fields=["school", "assignment", "student"]),
            models.Index(fields=["school", "status"]),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}"

    def clean(self):
        super().clean()

        required_relations = [self.school_id, self.assignment_id, self.student_id]
        if not all(required_relations):
            return

        if self.student.role != UserRole.STUDENT:
            raise ValidationError({"student": "Submission owner must have student role."})

        if self.student.school_id != self.school_id:
            raise ValidationError({"student": "Student must belong to the submission school."})

        if self.assignment.school_id != self.school_id:
            raise ValidationError(
                {"assignment": "Assignment must belong to the submission school."}
            )

        is_enrolled = StudentEnrollment.objects.filter(
            school=self.school,
            student=self.student,
            class_arm=self.assignment.class_arm,
            is_active=True,
        ).exists()
        if not is_enrolled:
            raise ValidationError(
                {"student": "Student is not enrolled in the assignment class arm."}
            )

        if self.question_order:
            assignment_question_ids = set(
                self.assignment.assignment_questions.values_list("id", flat=True)
            )
            if len(self.question_order) != len(set(self.question_order)):
                raise ValidationError(
                    {"question_order": "Question order cannot contain duplicates."}
                )
            stored_ids = set(self.question_order)
            if stored_ids != assignment_question_ids:
                raise ValidationError(
                    {"question_order": "Question order must match assignment questions."}
                )


class StudentAnswer(TimeStampedModel):
    submission = models.ForeignKey(
        Submission,
        related_name="answers",
        on_delete=models.CASCADE,
    )
    assignment_question = models.ForeignKey(
        "assignments.AssignmentQuestion",
        related_name="student_answers",
        on_delete=models.CASCADE,
    )
    selected_option = models.ForeignKey(
        "question_bank.QuestionOption",
        related_name="student_answers",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["assignment_question__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "assignment_question"],
                name="unique_answer_per_submission_assignment_question",
            )
        ]

    def __str__(self):
        return f"{self.submission_id} - {self.assignment_question_id}"

    def clean(self):
        super().clean()

        if not self.submission_id or not self.assignment_question_id:
            return

        if self.assignment_question.assignment_id != self.submission.assignment_id:
            raise ValidationError(
                {
                    "assignment_question": (
                        "Assignment question must belong to the submission assignment."
                    )
                }
            )

        if (
            self.selected_option_id
            and self.selected_option.question_id != self.assignment_question.question_id
        ):
            raise ValidationError(
                {
                    "selected_option": (
                        "Selected option must belong to the assignment question."
                    )
                }
            )
