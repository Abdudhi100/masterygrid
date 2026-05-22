from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.choices import UserRole
from apps.common.models import TimeStampedModel


class TermName(models.TextChoices):
    FIRST = "first", "First Term"
    SECOND = "second", "Second Term"
    THIRD = "third", "Third Term"


class JambRelevanceLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class AcademicSession(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="academic_sessions",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=32)
    starts_at = models.DateField()
    ends_at = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_at", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_academic_session_name_per_school",
            ),
            models.UniqueConstraint(
                fields=["school"],
                condition=models.Q(is_active=True),
                name="unique_active_academic_session_per_school",
            ),
        ]

    def __str__(self):
        return f"{self.school.name} - {self.name}"

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.starts_at > self.ends_at:
            raise ValidationError({"ends_at": "End date must be after start date."})


class Term(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="terms",
        on_delete=models.CASCADE,
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        related_name="terms",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=16, choices=TermName.choices)
    starts_at = models.DateField()
    ends_at = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["academic_session", "starts_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_session", "name"],
                name="unique_term_name_per_session_school",
            ),
            models.UniqueConstraint(
                fields=["school"],
                condition=models.Q(is_active=True),
                name="unique_active_term_per_school",
            ),
        ]

    def __str__(self):
        return f"{self.academic_session.name} - {self.get_name_display()}"

    def clean(self):
        super().clean()
        if (
            self.academic_session_id
            and self.school_id
            and self.academic_session.school_id != self.school_id
        ):
            raise ValidationError(
                {"academic_session": "Term must belong to the selected school's session."}
            )

        if self.starts_at and self.ends_at and self.starts_at > self.ends_at:
            raise ValidationError({"ends_at": "End date must be after start date."})


class ClassLevel(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="class_levels",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_class_level_name_per_school",
            )
        ]

    def __str__(self):
        return f"{self.school.name} - {self.name}"


class ClassArm(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="class_arms",
        on_delete=models.CASCADE,
    )
    class_level = models.ForeignKey(
        ClassLevel,
        related_name="class_arms",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school", "class_level", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "class_level", "name"],
                name="unique_class_arm_name_per_level_school",
            )
        ]

    def __str__(self):
        return f"{self.class_level.name} {self.name}"

    def clean(self):
        super().clean()
        if (
            self.class_level_id
            and self.school_id
            and self.class_level.school_id != self.school_id
        ):
            raise ValidationError(
                {"class_level": "Class level must belong to the selected school."}
            )


class Subject(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="subjects",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    is_jamb_subject = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_subject_name_per_school",
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(school__isnull=True),
                name="unique_global_subject_name",
            ),
        ]

    def __str__(self):
        scope = self.school.name if self.school_id else "Global"
        return f"{self.name} ({scope})"


class Topic(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="topics",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    subject = models.ForeignKey(
        Subject,
        related_name="topics",
        on_delete=models.PROTECT,
    )
    class_level = models.ForeignKey(
        ClassLevel,
        related_name="topics",
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    curriculum_tags = models.JSONField(default=list, blank=True)
    jamb_relevance_level = models.CharField(
        max_length=16,
        choices=JambRelevanceLevel.choices,
        default=JambRelevanceLevel.MEDIUM,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["subject", "class_level", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "subject", "class_level", "title"],
                name="unique_topic_title_per_subject_level_school",
            ),
            models.UniqueConstraint(
                fields=["subject", "class_level", "title"],
                condition=models.Q(school__isnull=True),
                name="unique_global_topic_title_per_subject_level",
            ),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.class_level.name} - {self.title}"

    def clean(self):
        super().clean()

        if self.school_id:
            if self.class_level_id and self.class_level.school_id != self.school_id:
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
        elif self.subject_id and self.subject.school_id:
            raise ValidationError(
                {"subject": "Global topics must use a global subject."}
            )


class TeacherClassSubjectAssignment(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="teacher_class_subject_assignments",
        on_delete=models.CASCADE,
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="teaching_assignments",
        on_delete=models.CASCADE,
    )
    class_arm = models.ForeignKey(
        ClassArm,
        related_name="teacher_assignments",
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        Subject,
        related_name="teacher_assignments",
        on_delete=models.PROTECT,
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        related_name="teacher_assignments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    term = models.ForeignKey(
        Term,
        related_name="teacher_assignments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school", "class_arm", "subject", "teacher"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "teacher",
                    "class_arm",
                    "subject",
                    "academic_session",
                    "term",
                ],
                name="unique_teacher_class_subject_session_term",
                nulls_distinct=False,
            )
        ]

    def __str__(self):
        return f"{self.teacher.full_name} - {self.class_arm} - {self.subject.name}"

    def clean(self):
        super().clean()

        if self.teacher_id:
            if self.teacher.role != UserRole.TEACHER:
                raise ValidationError({"teacher": "Assigned user must have teacher role."})
            if self.school_id and self.teacher.school_id != self.school_id:
                raise ValidationError(
                    {"teacher": "Teacher must belong to the selected school."}
                )

        if (
            self.class_arm_id
            and self.school_id
            and self.class_arm.school_id != self.school_id
        ):
            raise ValidationError(
                {"class_arm": "Class arm must belong to the selected school."}
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
            self.academic_session_id
            and self.school_id
            and self.academic_session.school_id != self.school_id
        ):
            raise ValidationError(
                {"academic_session": "Academic session must belong to the selected school."}
            )

        if self.term_id:
            if self.school_id and self.term.school_id != self.school_id:
                raise ValidationError({"term": "Term must belong to the selected school."})
            if (
                self.academic_session_id
                and self.term.academic_session_id != self.academic_session_id
            ):
                raise ValidationError(
                    {"term": "Term must belong to the selected academic session."}
                )


class StudentEnrollment(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="student_enrollments",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="student_enrollments",
        on_delete=models.CASCADE,
    )
    class_arm = models.ForeignKey(
        ClassArm,
        related_name="student_enrollments",
        on_delete=models.CASCADE,
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        related_name="student_enrollments",
        on_delete=models.CASCADE,
    )
    term = models.ForeignKey(
        Term,
        related_name="student_enrollments",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["school", "class_arm", "student"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_session", "term"],
                name="unique_student_enrollment_per_session_term",
                nulls_distinct=False,
            )
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.class_arm}"

    def clean(self):
        super().clean()

        if self.student_id:
            if self.student.role != UserRole.STUDENT:
                raise ValidationError({"student": "Enrolled user must have student role."})
            if self.school_id and self.student.school_id != self.school_id:
                raise ValidationError(
                    {"student": "Student must belong to the selected school."}
                )

        if (
            self.class_arm_id
            and self.school_id
            and self.class_arm.school_id != self.school_id
        ):
            raise ValidationError(
                {"class_arm": "Class arm must belong to the selected school."}
            )

        if (
            self.academic_session_id
            and self.school_id
            and self.academic_session.school_id != self.school_id
        ):
            raise ValidationError(
                {"academic_session": "Academic session must belong to the selected school."}
            )

        if self.term_id:
            if self.school_id and self.term.school_id != self.school_id:
                raise ValidationError({"term": "Term must belong to the selected school."})
            if self.term.academic_session_id != self.academic_session_id:
                raise ValidationError(
                    {"term": "Term must belong to the selected academic session."}
                )


class LessonLog(TimeStampedModel):
    school = models.ForeignKey(
        "schools.School",
        related_name="lesson_logs",
        on_delete=models.CASCADE,
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="lesson_logs",
        on_delete=models.CASCADE,
    )
    class_arm = models.ForeignKey(
        ClassArm,
        related_name="lesson_logs",
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        Subject,
        related_name="lesson_logs",
        on_delete=models.PROTECT,
    )
    topic = models.ForeignKey(
        Topic,
        related_name="lesson_logs",
        on_delete=models.PROTECT,
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        related_name="lesson_logs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    term = models.ForeignKey(
        Term,
        related_name="lesson_logs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    taught_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-taught_at", "-created_at"]

    def __str__(self):
        return f"{self.teacher.full_name} taught {self.topic.title} to {self.class_arm}"

    @property
    def can_generate_assignment(self):
        return bool(self.pk)

    def clean(self):
        super().clean()

        required_relations = [
            self.school_id,
            self.teacher_id,
            self.class_arm_id,
            self.subject_id,
            self.topic_id,
        ]
        if not all(required_relations):
            return

        from apps.academics.services import validate_teacher_can_log_lesson

        validate_teacher_can_log_lesson(
            user=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            academic_session=self.academic_session,
            term=self.term,
            school=self.school,
        )
