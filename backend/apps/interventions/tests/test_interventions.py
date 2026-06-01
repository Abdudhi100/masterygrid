from django.test import TestCase
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
from apps.common.choices import UserRole
from apps.interventions.models import InterventionStatus, StudentIntervention
from apps.schools.models import School


class InterventionApiTests(TestCase):
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
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123",
            full_name="Demo Teacher",
            role=UserRole.TEACHER,
            school=self.school,
        )
        self.unrelated_teacher = User.objects.create_user(
            email="unrelated-teacher@example.com",
            password="StrongPass123",
            full_name="Unrelated Teacher",
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
        self.unrelated_student = User.objects.create_user(
            email="unrelated-student@example.com",
            password="StrongPass123",
            full_name="Unrelated Student",
            role=UserRole.STUDENT,
            school=self.school,
        )
        self.other_student = User.objects.create_user(
            email="other-student@example.com",
            password="StrongPass123",
            full_name="Other Student",
            role=UserRole.STUDENT,
            school=self.other_school,
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
        self.other_class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=self.class_level,
            name="Science B",
        )
        self.subject = Subject.objects.create(name="Mathematics", code="MTH")
        self.topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Quadratic Equations",
        )
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
        )
        StudentEnrollment.objects.create(
            school=self.school,
            student=self.student,
            class_arm=self.class_arm,
            academic_session=self.session,
        )
        StudentEnrollment.objects.create(
            school=self.school,
            student=self.unrelated_student,
            class_arm=self.other_class_arm,
            academic_session=self.session,
        )

        self.other_session = AcademicSession.objects.create(
            school=self.other_school,
            name="2026/2027",
            starts_at="2026-09-01",
            ends_at="2027-07-31",
            is_active=True,
        )
        self.other_class_level = ClassLevel.objects.create(
            school=self.other_school,
            name="SS2",
        )
        self.other_class_arm = ClassArm.objects.create(
            school=self.other_school,
            class_level=self.other_class_level,
            name="Science A",
        )
        StudentEnrollment.objects.create(
            school=self.other_school,
            student=self.other_student,
            class_arm=self.other_class_arm,
            academic_session=self.other_session,
        )

        self.client = APIClient()

    def intervention_payload(self, student=None, **overrides):
        payload = {
            "student": (student or self.student).id,
            "title": "Parent follow-up for weak topic",
            "description": "Discuss recent weak performance and agree next action.",
            "category": "parent_contact",
            "priority": "high",
            "status": "open",
            "source_type": "manual",
        }
        payload.update(overrides)
        return payload

    def test_school_admin_can_create_and_view_own_school_intervention(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/interventions/",
            self.intervention_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["school"], self.school.id)
        self.assertEqual(response.data["student"], self.student.id)
        self.assertEqual(response.data["status"], "open")

        list_response = self.client.get("/api/interventions/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["student_name"], "Demo Student")

    def test_school_admin_cannot_view_cross_school_intervention(self):
        StudentIntervention.objects.create(
            school=self.school,
            student=self.student,
            created_by=self.admin,
            title="Own school",
        )
        StudentIntervention.objects.create(
            school=self.other_school,
            student=self.other_student,
            created_by=self.other_admin,
            title="Other school",
        )
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/interventions/")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Own school"])

    def test_school_admin_can_list_student_interventions(self):
        StudentIntervention.objects.create(
            school=self.school,
            student=self.student,
            created_by=self.admin,
            title="Student plan",
        )
        self.client.force_authenticate(self.admin)

        response = self.client.get(f"/api/interventions/student/{self.student.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Student plan")

    def test_teacher_can_create_for_student_they_teach(self):
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            "/api/interventions/",
            self.intervention_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["student"], self.student.id)
        self.assertEqual(response.data["created_by"], self.teacher.id)

    def test_teacher_cannot_create_for_unrelated_student(self):
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            "/api/interventions/",
            self.intervention_payload(student=self.unrelated_student),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("student", response.data)

    def test_student_is_blocked(self):
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/interventions/")

        self.assertEqual(response.status_code, 403)

    def test_add_note_works_for_accessible_intervention(self):
        intervention = StudentIntervention.objects.create(
            school=self.school,
            student=self.student,
            created_by=self.admin,
            title="Revision class",
        )
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            f"/api/interventions/{intervention.id}/add-note/",
            {"note": "Student attended the first revision session."},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(intervention.notes.count(), 1)
        self.assertEqual(response.data["author"], self.teacher.id)

    def test_resolved_status_sets_completed_at(self):
        intervention = StudentIntervention.objects.create(
            school=self.school,
            student=self.student,
            created_by=self.admin,
            title="Follow-up",
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/interventions/{intervention.id}/",
            {"status": InterventionStatus.RESOLVED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        intervention.refresh_from_db()
        self.assertEqual(intervention.status, InterventionStatus.RESOLVED)
        self.assertIsNotNone(intervention.completed_at)

    def test_create_from_progress_report_works(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/interventions/create-from-progress-report/",
            {
                "student": self.student.id,
                "title": "Progress report follow-up",
                "description": "Create a short improvement plan.",
                "priority": "medium",
                "recommended_action": "Assign focused practice.",
                "source_subject": self.subject.id,
                "source_topic": self.topic.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["source_type"], "progress_report")
        self.assertEqual(response.data["source_subject"], self.subject.id)
        self.assertEqual(response.data["source_topic"], self.topic.id)
