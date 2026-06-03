from django.conf import settings
from django.db import models


class AuditCategory(models.TextChoices):
    AUTH = "auth", "Auth"
    ACADEMICS = "academics", "Academics"
    QUESTION_BANK = "question_bank", "Question Bank"
    ASSIGNMENT = "assignment", "Assignment"
    SUBMISSION = "submission", "Submission"
    INTERVENTION = "intervention", "Intervention"
    NOTIFICATION = "notification", "Notification"
    IMPORT = "import", "Import"
    USER_MANAGEMENT = "user_management", "User Management"
    SYSTEM = "system", "System"


class AuditLog(models.Model):
    school = models.ForeignKey(
        "schools.School",
        related_name="audit_logs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    actor_email = models.EmailField(blank=True)
    actor_role = models.CharField(max_length=32, blank=True)
    action = models.CharField(max_length=64, db_index=True)
    category = models.CharField(
        max_length=32,
        choices=AuditCategory.choices,
        db_index=True,
    )
    object_type = models.CharField(max_length=128, blank=True, db_index=True)
    object_id = models.CharField(max_length=64, blank=True, db_index=True)
    object_repr = models.CharField(max_length=255, blank=True)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="targeted_audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    target_user_email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school", "category", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["target_user", "created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        actor = self.actor_email or "system"
        target = self.object_repr or self.object_id or self.object_type
        return f"{actor} {self.action} {target}".strip()
