from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
from apps.accounts.models import User
from apps.common.choices import UserRole
from apps.schools.models import School


class AcademicsModelValidationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123",
            full_name="Demo Teacher",
            role=UserRole.TEACHER,
            school=self.school,
        )
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            starts_at="2026-09-01",
            ends_at="2027-07-31",
            is_active=True,
        )
        self.term = Term.objects.create(
            school=self.school,
            academic_session=self.session,
            name="first",
            starts_at="2026-09-01",
            ends_at="2026-12-15",
            is_active=True,
        )
        self.class_level = ClassLevel.objects.create(
            school=self.school,
            name="SS2",
        )
        self.class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=self.class_level,
            name="Science A",
        )
        self.subject = Subject.objects.create(
            name="Mathematics",
            code="MTH",
            is_jamb_subject=True,
        )
        self.topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Quadratic Equations",
            jamb_relevance_level="high",
        )

    def test_assigned_teacher_can_log_lesson(self):
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            academic_session=self.session,
            term=self.term,
        )
        lesson_log = LessonLog(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            academic_session=self.session,
            term=self.term,
            taught_at=timezone.now(),
        )

        lesson_log.full_clean()

    def test_teacher_must_be_assigned_before_logging_lesson(self):
        lesson_log = LessonLog(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            academic_session=self.session,
            term=self.term,
            taught_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            lesson_log.full_clean()

    def test_topic_must_match_lesson_subject(self):
        other_subject = Subject.objects.create(name="Physics", code="PHY")
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=other_subject,
            academic_session=self.session,
            term=self.term,
        )
        lesson_log = LessonLog(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=other_subject,
            topic=self.topic,
            academic_session=self.session,
            term=self.term,
            taught_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            lesson_log.full_clean()
