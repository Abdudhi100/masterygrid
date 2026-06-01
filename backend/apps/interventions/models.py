from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.choices import UserRole
from apps.common.models import TimeStampedModel


class InterventionCategory(models.TextChoices):
    ACADEMIC_SUPPORT = "academic_support", "Academic Support"
    PARENT_CONTACT = "parent_contact", "Parent Contact"
    REMEDIAL_ASSIGNMENT = "remedial_assignment", "Remedial Assignment"
    REVISION_CLASS = "revision_class", "Revision Class"
    ATTENDANCE_FOLLOWUP = "attendance_followup", "Attendance Follow-up"
    BEHAVIOR_FOLLOWUP = "behavior_followup", "Behavior Follow-up"
    OTHER = "other", "Other"


class InterventionPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class InterventionStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class InterventionSourceType(models.TextChoices):
    MANUAL = "manual", "Manual"
    WEAK_STUDENT = "weak_student", "Weak Student"
    WEAK_TOPIC = "weak_topic", "Weak Topic"
    PROGRESS_REPORT = "progress_report", "Progress Report"
    REMEDIATION_PLAN = "remediation_plan", "Remediation Plan"
    ADMIN_INTERVENTION_DASHBOARD = (
        "admin_intervention_dashboard",
        "Admin Intervention Dashboard",
    )


class StudentIntervention(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="student_interventions",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="student_interventions",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_interventions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assigned_interventions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=32,
        choices=InterventionCategory.choices,
        default=InterventionCategory.ACADEMIC_SUPPORT,
    )
    priority = models.CharField(
        max_length=16,
        choices=InterventionPriority.choices,
        default=InterventionPriority.MEDIUM,
    )
    status = models.CharField(
        max_length=16,
        choices=InterventionStatus.choices,
        default=InterventionStatus.OPEN,
    )
    source_type = models.CharField(
        max_length=64,
        choices=InterventionSourceType.choices,
        default=InterventionSourceType.MANUAL,
    )
    source_assignment = models.ForeignKey(
        "assignments.Assignment",
        related_name="student_interventions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    source_subject = models.ForeignKey(
        "academics.Subject",
        related_name="student_interventions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    source_topic = models.ForeignKey(
        "academics.Topic",
        related_name="student_interventions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    source_class_arm = models.ForeignKey(
        "academics.ClassArm",
        related_name="student_interventions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=["school", "student", "status"]),
            models.Index(fields=["school", "status", "priority"]),
            models.Index(fields=["school", "due_date"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.student.full_name}"

    def clean(self):
        super().clean()

        if self.title is not None and not self.title.strip():
            raise ValidationError({"title": "Intervention title cannot be blank."})

        if self.student_id:
            if self.student.role != UserRole.STUDENT:
                raise ValidationError({"student": "Intervention target must be a student."})
            if self.school_id and self.student.school_id != self.school_id:
                raise ValidationError(
                    {"student": "Student must belong to the intervention school."}
                )

        if self.created_by_id and self.created_by.role != UserRole.PLATFORM_ADMIN:
            if self.school_id and self.created_by.school_id != self.school_id:
                raise ValidationError(
                    {"created_by": "Creator must belong to the intervention school."}
                )

        if self.assigned_to_id:
            if self.assigned_to.role == UserRole.STUDENT:
                raise ValidationError(
                    {"assigned_to": "Interventions cannot be assigned to students."}
                )
            if self.assigned_to.role != UserRole.PLATFORM_ADMIN:
                if self.school_id and self.assigned_to.school_id != self.school_id:
                    raise ValidationError(
                        {"assigned_to": "Assigned user must belong to this school."}
                    )

        if self.source_assignment_id and self.school_id:
            if self.source_assignment.school_id != self.school_id:
                raise ValidationError(
                    {
                        "source_assignment": (
                            "Source assignment must belong to the intervention school."
                        )
                    }
                )

        if self.source_class_arm_id and self.school_id:
            if self.source_class_arm.school_id != self.school_id:
                raise ValidationError(
                    {"source_class_arm": "Source class arm must belong to this school."}
                )

        if self.source_subject_id and self.school_id:
            if (
                self.source_subject.school_id
                and self.source_subject.school_id != self.school_id
            ):
                raise ValidationError(
                    {
                        "source_subject": (
                            "Source subject must be global or belong to this school."
                        )
                    }
                )

        if self.source_topic_id and self.school_id:
            if self.source_topic.school_id and self.source_topic.school_id != self.school_id:
                raise ValidationError(
                    {"source_topic": "Source topic must be global or belong to this school."}
                )
            if (
                self.source_subject_id
                and self.source_topic.subject_id != self.source_subject_id
            ):
                raise ValidationError(
                    {"source_topic": "Source topic must match the source subject."}
                )

    def save(self, *args, **kwargs):
        if self.status in {InterventionStatus.RESOLVED, InterventionStatus.CLOSED}:
            if self.completed_at is None:
                self.completed_at = timezone.now()
        elif self.completed_at is not None:
            self.completed_at = None

        self.full_clean()
        super().save(*args, **kwargs)


class InterventionNote(TimeStampedModel):
    intervention = models.ForeignKey(
        StudentIntervention,
        related_name="notes",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="intervention_notes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    note = models.TextField()
    is_internal = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.intervention_id} by {self.author_id}"

    def clean(self):
        super().clean()

        if not self.note or not self.note.strip():
            raise ValidationError({"note": "Note cannot be blank."})

        if self.author_id and self.author.role != UserRole.PLATFORM_ADMIN:
            if self.author.school_id != self.intervention.school_id:
                raise ValidationError(
                    {"author": "Note author must belong to the intervention school."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
