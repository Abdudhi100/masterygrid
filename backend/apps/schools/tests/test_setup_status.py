from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School


class SchoolSetupStatusTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.other_school = School.objects.create(
            name="Other College",
            slug="other-college",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123",
            full_name="Demo Admin",
            role=UserRole.SCHOOL_ADMIN,
            school=self.school,
        )
        self.other_admin = User.objects.create_user(
            email="other-admin@example.com",
            password="StrongPass123",
            full_name="Other Admin",
            role=UserRole.SCHOOL_ADMIN,
            school=self.other_school,
        )
        self.platform_admin = User.objects.create_user(
            email="platform@example.com",
            password="StrongPass123",
            full_name="Platform Admin",
            role=UserRole.PLATFORM_ADMIN,
            is_staff=True,
        )
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123",
            full_name="Demo Teacher",
            role=UserRole.TEACHER,
            school=self.school,
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            full_name="Demo Student",
            role=UserRole.STUDENT,
            school=self.school,
        )
        self.client = APIClient()

    def setup_minimum_school_data(self):
        session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            starts_at="2026-09-01",
            ends_at="2027-07-31",
            is_active=True,
        )
        term = Term.objects.create(
            school=self.school,
            academic_session=session,
            name="first",
            starts_at="2026-09-01",
            ends_at="2026-12-15",
            is_active=True,
        )
        class_level = ClassLevel.objects.create(school=self.school, name="SS2")
        class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=class_level,
            name="Science A",
        )
        subject = Subject.objects.create(
            school=self.school,
            name="Physics",
            code="PHY",
            is_active=True,
        )
        topic = Topic.objects.create(
            school=self.school,
            subject=subject,
            class_level=class_level,
            title="Motion",
        )
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.teacher,
            class_arm=class_arm,
            subject=subject,
            academic_session=session,
            term=term,
            is_active=True,
        )
        StudentEnrollment.objects.create(
            school=self.school,
            student=self.student,
            class_arm=class_arm,
            academic_session=session,
            term=term,
            is_active=True,
        )
        question = Question.objects.create(
            school=self.school,
            subject=subject,
            topic=topic,
            class_level=class_level,
            question_text="Which option describes motion?",
            explanation="Motion is a change in position over time.",
            difficulty="easy",
            status=QuestionStatus.APPROVED,
            is_active=True,
            created_by=self.teacher,
        )
        for label in ["A", "B", "C", "D"]:
            QuestionOption.objects.create(
                question=question,
                label=label,
                text=f"Option {label}",
                is_correct=label == "A",
            )

    def test_school_admin_gets_incomplete_own_school_status(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/schools/setup-status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school_id"], self.school.id)
        self.assertFalse(response.data["is_setup_complete"])
        self.assertEqual(response.data["completion_percentage"], 18)
        self.assertEqual(len(response.data["steps"]), 11)
        self.assertEqual(response.data["next_step"]["key"], "academic_session")

    def test_completed_school_returns_complete_status(self):
        self.setup_minimum_school_data()
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/schools/setup-status/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_setup_complete"])
        self.assertEqual(response.data["completion_percentage"], 100)
        self.assertIsNone(response.data["next_step"])
        self.assertEqual(response.data["blocking_issues"], [])

    def test_teacher_student_and_anonymous_are_blocked(self):
        self.client.force_authenticate(self.teacher)
        teacher_response = self.client.get("/api/schools/setup-status/")
        self.client.force_authenticate(self.student)
        student_response = self.client.get("/api/schools/setup-status/")
        self.client.force_authenticate(None)
        anonymous_response = self.client.get("/api/schools/setup-status/")

        self.assertEqual(teacher_response.status_code, 403)
        self.assertEqual(student_response.status_code, 403)
        self.assertEqual(anonymous_response.status_code, 401)

    def test_platform_admin_can_request_school_scope(self):
        self.setup_minimum_school_data()
        self.client.force_authenticate(self.platform_admin)

        response = self.client.get(
            "/api/schools/setup-status/",
            {"school": self.school.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school_id"], self.school.id)
        self.assertTrue(response.data["is_setup_complete"])

    def test_platform_admin_without_school_scope_gets_validation_error(self):
        self.client.force_authenticate(self.platform_admin)

        response = self.client.get("/api/schools/setup-status/")

        self.assertEqual(response.status_code, 400)
        self.assertIn("school", response.data)

    def test_school_admin_cannot_switch_to_other_school_with_query_param(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(
            "/api/schools/setup-status/",
            {"school": self.other_school.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school_id"], self.school.id)
