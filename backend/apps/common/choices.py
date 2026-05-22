from django.db import models


class UserRole(models.TextChoices):
    PLATFORM_ADMIN = "platform_admin", "Platform Admin"
    SCHOOL_ADMIN = "school_admin", "School Admin"
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"


class QuestionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    ARCHIVED = "archived", "Archived"


class AssignmentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class SubmissionStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    IN_PROGRESS = "in_progress", "In Progress"
    SUBMITTED = "submitted", "Submitted"
    GRADED = "graded", "Graded"
    AUTO_SUBMITTED = "auto_submitted", "Auto Submitted"
