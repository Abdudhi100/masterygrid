from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.choices import QuestionStatus
from apps.common.models import TimeStampedModel


class QuestionSourceType(models.TextChoices):
    JAMB_PAST_QUESTION = "jamb_past_question", "JAMB Past Question"
    WAEC_PAST_QUESTION = "waec_past_question", "WAEC Past Question"
    NECO_PAST_QUESTION = "neco_past_question", "NECO Past Question"
    TEACHER_CREATED = "teacher_created", "Teacher Created"
    AI_GENERATED = "ai_generated", "AI Generated"
    SCHOOL_CREATED = "school_created", "School Created"


class QuestionDifficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class QuestionOptionLabel(models.TextChoices):
    A = "A", "A"
    B = "B", "B"
    C = "C", "C"
    D = "D", "D"


class QuestionImportFileType(models.TextChoices):
    CSV = "csv", "CSV"
    XLSX = "xlsx", "Excel"
    JSON = "json", "JSON"


class QuestionImportBatchStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed With Errors"
    FAILED = "failed", "Failed"


class QuestionImportRowStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IMPORTED = "imported", "Imported"
    FAILED = "failed", "Failed"
    DUPLICATE = "duplicate", "Duplicate"


class QuestionSource(TimeStampedModel):
    name = models.CharField(max_length=255)
    source_type = models.CharField(
        max_length=32,
        choices=QuestionSourceType.choices,
    )
    exam_body = models.CharField(max_length=32, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "-year"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "source_type", "year"],
                name="unique_question_source_name_type_year",
                nulls_distinct=False,
            )
        ]

    def __str__(self):
        if self.year:
            return f"{self.name} ({self.year})"
        return self.name


class Question(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="questions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    subject = models.ForeignKey(
        "academics.Subject",
        related_name="questions",
        on_delete=models.PROTECT,
    )
    topic = models.ForeignKey(
        "academics.Topic",
        related_name="questions",
        on_delete=models.PROTECT,
    )
    class_level = models.ForeignKey(
        "academics.ClassLevel",
        related_name="questions",
        on_delete=models.PROTECT,
    )
    source = models.ForeignKey(
        QuestionSource,
        related_name="questions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)
    difficulty = models.CharField(
        max_length=16,
        choices=QuestionDifficulty.choices,
        default=QuestionDifficulty.MEDIUM,
    )
    status = models.CharField(
        max_length=16,
        choices=QuestionStatus.choices,
        default=QuestionStatus.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_questions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviewed_questions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "subject", "topic", "class_level"]),
            models.Index(fields=["status", "is_active"]),
        ]

    def __str__(self):
        return self.question_text[:80]

    @property
    def is_usable_for_assignment(self):
        return self.is_active and self.status == QuestionStatus.APPROVED

    def clean(self):
        super().clean()

        if self.question_text is not None and not self.question_text.strip():
            raise ValidationError({"question_text": "Question text cannot be blank."})

        if self.topic_id and self.subject_id and self.topic.subject_id != self.subject_id:
            raise ValidationError({"topic": "Topic must belong to the selected subject."})

        if (
            self.topic_id
            and self.class_level_id
            and self.topic.class_level_id != self.class_level_id
        ):
            raise ValidationError(
                {"topic": "Topic class level must match the selected class level."}
            )

        if self.school_id:
            if (
                self.class_level_id
                and self.class_level.school_id != self.school_id
            ):
                raise ValidationError(
                    {"class_level": "Class level must belong to the selected school."}
                )

            if (
                self.subject_id
                and self.subject.school_id
                and self.subject.school_id != self.school_id
            ):
                raise ValidationError(
                    {"subject": "Subject must be global or belong to the selected school."}
                )

            if (
                self.topic_id
                and self.topic.school_id
                and self.topic.school_id != self.school_id
            ):
                raise ValidationError(
                    {"topic": "Topic must be global or belong to the selected school."}
                )
        else:
            if self.subject_id and self.subject.school_id:
                raise ValidationError(
                    {"subject": "Global questions must use a global subject."}
                )
            if self.topic_id and self.topic.school_id:
                raise ValidationError({"topic": "Global questions must use a global topic."})

        if self.reviewed_by_id and not self.reviewed_at:
            self.reviewed_at = timezone.now()


class QuestionOption(TimeStampedModel):
    question = models.ForeignKey(
        Question,
        related_name="options",
        on_delete=models.CASCADE,
    )
    label = models.CharField(max_length=1, choices=QuestionOptionLabel.choices)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "label"],
                name="unique_question_option_label",
            ),
            models.UniqueConstraint(
                fields=["question"],
                condition=models.Q(is_correct=True),
                name="unique_correct_option_per_question",
            ),
        ]

    def __str__(self):
        return f"{self.question_id} - {self.label}"

    def clean(self):
        super().clean()

        if self.text is not None and not self.text.strip():
            raise ValidationError({"text": "Option text cannot be blank."})

        if self.question_id and self.text:
            duplicate_exists = (
                QuestionOption.objects.filter(
                    question=self.question,
                    text__iexact=self.text.strip(),
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if duplicate_exists:
                raise ValidationError(
                    {"text": "Duplicate option text is not allowed for the same question."}
                )


class QuestionImportBatch(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="question_import_batches",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="question_import_batches",
        on_delete=models.PROTECT,
    )
    source = models.ForeignKey(
        QuestionSource,
        related_name="import_batches",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(
        max_length=16,
        choices=QuestionImportFileType.choices,
    )
    status = models.CharField(
        max_length=32,
        choices=QuestionImportBatchStatus.choices,
        default=QuestionImportBatchStatus.UPLOADED,
    )
    total_rows = models.PositiveIntegerField(default=0)
    successful_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    duplicate_rows = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["uploaded_by", "status"]),
        ]

    def __str__(self):
        return self.title


class QuestionImportRow(TimeStampedModel):
    batch = models.ForeignKey(
        QuestionImportBatch,
        related_name="rows",
        on_delete=models.CASCADE,
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    status = models.CharField(
        max_length=16,
        choices=QuestionImportRowStatus.choices,
        default=QuestionImportRowStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    question = models.ForeignKey(
        Question,
        related_name="import_rows",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    content_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["batch", "row_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "row_number"],
                name="unique_question_import_row_number_per_batch",
            )
        ]
        indexes = [
            models.Index(fields=["batch", "status"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        return f"{self.batch_id} - row {self.row_number}"
