from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.choices import UserRole
from apps.common.models import TimeStampedModel


class NotificationType(models.TextChoices):
    ASSIGNMENT_PUBLISHED = "assignment_published", "Assignment Published"
    ASSIGNMENT_DUE_SOON = "assignment_due_soon", "Assignment Due Soon"
    ASSIGNMENT_SUBMITTED = "assignment_submitted", "Assignment Submitted"
    LOW_SUBMISSION_RATE = "low_submission_rate", "Low Submission Rate"
    WEAK_TOPIC_DETECTED = "weak_topic_detected", "Weak Topic Detected"
    INTERVENTION_CREATED = "intervention_created", "Intervention Created"
    INTERVENTION_UPDATED = "intervention_updated", "Intervention Updated"
    INTERVENTION_NOTE_ADDED = "intervention_note_added", "Intervention Note Added"
    INTERVENTION_DUE = "intervention_due", "Intervention Due"
    PROGRESS_REPORT_AVAILABLE = (
        "progress_report_available",
        "Progress Report Available",
    )
    LEARNING_RECOMMENDATION = "learning_recommendation", "Learning Recommendation"
    SYSTEM = "system", "System"


class NotificationPriority(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class NotificationStatus(models.TextChoices):
    UNREAD = "unread", "Unread"
    READ = "read", "Read"
    ARCHIVED = "archived", "Archived"


class Notification(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actor_notifications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    notification_type = models.CharField(
        max_length=64,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    priority = models.CharField(
        max_length=16,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    status = models.CharField(
        max_length=16,
        choices=NotificationStatus.choices,
        default=NotificationStatus.UNREAD,
    )
    target_url = models.CharField(max_length=500, blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status", "created_at"]),
            models.Index(fields=["school", "notification_type", "created_at"]),
            models.Index(fields=["recipient", "priority", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"

    def clean(self):
        super().clean()

        if self.title is not None and not self.title.strip():
            raise ValidationError({"title": "Notification title cannot be blank."})

        if not self.recipient_id:
            raise ValidationError({"recipient": "Recipient is required."})

        if self.school_id and self.recipient_id:
            if (
                self.recipient.role != UserRole.PLATFORM_ADMIN
                and self.recipient.school_id != self.school_id
            ):
                raise ValidationError(
                    {"school": "Notification school must match recipient school."}
                )

        if self.actor_id and self.school_id:
            if self.actor.role != UserRole.PLATFORM_ADMIN and self.actor.school_id != self.school_id:
                raise ValidationError(
                    {"actor": "Notification actor must match the notification school."}
                )

    def save(self, *args, **kwargs):
        if not self.school_id and self.recipient_id and self.recipient.school_id:
            self.school = self.recipient.school

        if self.status == NotificationStatus.READ and self.read_at is None:
            self.read_at = timezone.now()
        elif self.status == NotificationStatus.UNREAD and self.read_at is not None:
            self.read_at = None

        self.full_clean()
        super().save(*args, **kwargs)
