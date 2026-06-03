from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Topic,
)
from apps.accounts.models import User
from apps.assignments.services import create_assignment_from_topic
from apps.audit.models import AuditLog
from apps.audit.services import record_audit_log
from apps.common.choices import QuestionStatus, UserRole
from apps.interventions.models import (
    InterventionCategory,
    InterventionPriority,
    InterventionSourceType,
    InterventionStatus,
    StudentIntervention,
)
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School


class AuditLogTests(TestCase):
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
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            starts_at="2026-09-01",
            ends_at="2027-07-31",
            is_active=True,
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name="SS2")
        self.class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=self.class_level,
            name="Science A",
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Physics",
            code="PHY",
            is_active=True,
        )
        self.topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Motion",
        )
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            academic_session=self.session,
            is_active=True,
        )
        StudentEnrollment.objects.create(
            school=self.school,
            student=self.student,
            class_arm=self.class_arm,
            academic_session=self.session,
            is_active=True,
        )
        self.client = APIClient()

    def create_question(self, *, status=QuestionStatus.DRAFT, text="Audit question?"):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            question_text=text,
            explanation="Audit explanation.",
            difficulty="medium",
            status=status,
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
        return question

    def create_assignment(self):
        for index in range(2):
            self.create_question(
                status=QuestionStatus.APPROVED,
                text=f"Approved audit question {index + 1}?",
            )
        return create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Audit Assignment",
            question_count=2,
            due_at=timezone.now() + timedelta(days=3),
        )

    def csv_upload(self, content):
        return SimpleUploadedFile(
            "users.csv",
            content.encode("utf-8"),
            content_type="text/csv",
        )

    def paginated_results(self, response):
        return response.data.get("results", response.data)

    def test_record_audit_log_scrubs_sensitive_metadata(self):
        log = record_audit_log(
            actor=self.admin,
            action="system_test",
            category="system",
            school=self.school,
            metadata={
                "password": "Secret123",
                "nested": {"access_token": "abc", "safe": "value"},
                "items": [{"refresh": "token"}],
            },
        )

        self.assertIsNotNone(log)
        log.refresh_from_db()
        self.assertEqual(log.metadata["password"], "[redacted]")
        self.assertEqual(log.metadata["nested"]["access_token"], "[redacted]")
        self.assertEqual(log.metadata["nested"]["safe"], "value")
        self.assertEqual(log.metadata["items"][0]["refresh"], "[redacted]")

    def test_school_admin_sees_only_own_school_logs(self):
        record_audit_log(
            actor=self.admin,
            action="own_action",
            category="system",
            school=self.school,
        )
        record_audit_log(
            actor=self.other_admin,
            action="other_action",
            category="system",
            school=self.other_school,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/audit/logs/")

        self.assertEqual(response.status_code, 200)
        actions = {row["action"] for row in self.paginated_results(response)}
        self.assertIn("own_action", actions)
        self.assertNotIn("other_action", actions)

    def test_platform_admin_sees_all_and_can_filter_school(self):
        record_audit_log(
            actor=self.admin,
            action="own_action",
            category="system",
            school=self.school,
        )
        record_audit_log(
            actor=self.other_admin,
            action="other_action",
            category="system",
            school=self.other_school,
        )
        self.client.force_authenticate(self.platform_admin)

        all_response = self.client.get("/api/audit/logs/")
        filtered_response = self.client.get(
            "/api/audit/logs/",
            {"school": self.school.id},
        )

        self.assertEqual(all_response.status_code, 200)
        self.assertEqual(filtered_response.status_code, 200)
        all_actions = {row["action"] for row in self.paginated_results(all_response)}
        filtered_actions = {
            row["action"] for row in self.paginated_results(filtered_response)
        }
        self.assertIn("own_action", all_actions)
        self.assertIn("other_action", all_actions)
        self.assertIn("own_action", filtered_actions)
        self.assertNotIn("other_action", filtered_actions)

    def test_teacher_student_and_anonymous_are_blocked(self):
        self.client.force_authenticate(self.teacher)
        teacher_response = self.client.get("/api/audit/logs/")
        self.client.force_authenticate(self.student)
        student_response = self.client.get("/api/audit/logs/")
        self.client.force_authenticate(None)
        anonymous_response = self.client.get("/api/audit/logs/")

        self.assertEqual(teacher_response.status_code, 403)
        self.assertEqual(student_response.status_code, 403)
        self.assertEqual(anonymous_response.status_code, 401)

    def test_question_approval_creates_audit_log(self):
        question = self.create_question()
        self.client.force_authenticate(self.admin)

        response = self.client.post(f"/api/question-bank/questions/{question.id}/approve/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="question_approved",
                category="question_bank",
                object_id=str(question.id),
                actor=self.admin,
            ).exists()
        )

    def test_user_registration_creates_audit_log(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new.student@example.com",
                "full_name": "New Student",
                "password": "StrongPass123",
                "role": UserRole.STUDENT,
                "school": self.school.id,
                "admission_number": "AUD-S-1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created_user_id = response.data["id"]
        self.assertTrue(
            AuditLog.objects.filter(
                action="user_created",
                category="user_management",
                target_user_id=created_user_id,
                metadata__role=UserRole.STUDENT,
            ).exists()
        )

    def test_assignment_publish_and_deadline_extension_create_audit_logs(self):
        assignment = self.create_assignment()
        self.client.force_authenticate(self.teacher)

        publish_response = self.client.post(f"/api/assignments/{assignment.id}/publish/")
        extension_response = self.client.post(
            f"/api/assignments/{assignment.id}/extend-deadline/",
            {
                "due_at": (timezone.now() + timedelta(days=5)).isoformat(),
                "allow_late_submissions": True,
                "late_submission_deadline": (
                    timezone.now() + timedelta(days=6)
                ).isoformat(),
            },
            format="json",
        )

        self.assertEqual(publish_response.status_code, 200)
        self.assertEqual(extension_response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action="assignment_published",
                object_id=str(assignment.id),
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="assignment_deadline_extended",
                object_id=str(assignment.id),
            ).exists()
        )

    def test_intervention_note_creates_audit_log(self):
        intervention = StudentIntervention.objects.create(
            school=self.school,
            student=self.student,
            created_by=self.admin,
            title="Follow up",
            description="Support needed.",
            category=InterventionCategory.ACADEMIC_SUPPORT,
            priority=InterventionPriority.HIGH,
            status=InterventionStatus.OPEN,
            source_type=InterventionSourceType.MANUAL,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            f"/api/interventions/{intervention.id}/add-note/",
            {"note": "Parent contacted.", "is_internal": True},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(
                action="intervention_note_added",
                target_user=self.student,
                metadata__intervention=intervention.id,
            ).exists()
        )

    def test_bulk_user_import_creates_audit_log(self):
        upload = self.csv_upload(
            "\n".join(
                [
                    "full_name,email,staff_id,phone_number,password",
                    "Audit Teacher,audit.teacher@example.com,AUD-T-1,08000000000,StrongPass123",
                ]
            )
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/imports/",
            {"import_type": "teachers", "file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(
                action="bulk_import_created",
                category="import",
                metadata__import_domain="accounts",
                metadata__import_type="teachers",
            ).exists()
        )
