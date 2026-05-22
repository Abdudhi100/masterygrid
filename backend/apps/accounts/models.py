from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.choices import UserRole
from apps.common.models import TimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")

        email = self.normalize_email(email)
        extra_fields.setdefault("role", UserRole.STUDENT)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.PLATFORM_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("role") != UserRole.PLATFORM_ADMIN:
            raise ValueError("Superuser must have role=platform_admin.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    school = models.ForeignKey(
        "schools.School",
        related_name="users",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        self.email = UserManager.normalize_email(self.email)

        if self.role != UserRole.PLATFORM_ADMIN and not self.school_id:
            raise ValidationError(
                {"school": "School is required for school admins, teachers, and students."}
            )


class TeacherProfile(TimeStampedModel):
    user = models.OneToOneField(
        User,
        related_name="teacher_profile",
        on_delete=models.CASCADE,
    )
    school = models.ForeignKey(
        "schools.School",
        related_name="teacher_profiles",
        on_delete=models.PROTECT,
    )
    staff_id = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["staff_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "staff_id"],
                name="unique_teacher_staff_id_per_school",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} ({self.staff_id})"

    def clean(self):
        super().clean()

        if self.user_id and self.user.role != UserRole.TEACHER:
            raise ValidationError({"user": "TeacherProfile user must have teacher role."})

        if self.user_id and self.user.school_id != self.school_id:
            raise ValidationError({"school": "Profile school must match the user's school."})


class StudentProfile(TimeStampedModel):
    user = models.OneToOneField(
        User,
        related_name="student_profile",
        on_delete=models.CASCADE,
    )
    school = models.ForeignKey(
        "schools.School",
        related_name="student_profiles",
        on_delete=models.PROTECT,
    )
    admission_number = models.CharField(max_length=64)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_phone = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["admission_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "admission_number"],
                name="unique_student_admission_number_per_school",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} ({self.admission_number})"

    def clean(self):
        super().clean()

        if self.user_id and self.user.role != UserRole.STUDENT:
            raise ValidationError({"user": "StudentProfile user must have student role."})

        if self.user_id and self.user.school_id != self.school_id:
            raise ValidationError({"school": "Profile school must match the user's school."})
