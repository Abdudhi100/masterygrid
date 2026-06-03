from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import (
    AcademicImportBatch,
    AcademicSession,
    ClassArm,
    ClassLevel,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
)
from apps.accounts.models import StudentProfile, TeacherProfile, User
from apps.common.choices import UserRole
from apps.schools.models import School


def csv_upload(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


class AcademicBulkImportTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.other_school = School.objects.create(name="Other College", slug="other-college")
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123",
            full_name="Demo Admin",
            role=UserRole.SCHOOL_ADMIN,
            school=self.school,
        )
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123",
            full_name="Demo Teacher",
            role=UserRole.TEACHER,
            school=self.school,
        )
        TeacherProfile.objects.create(
            user=self.teacher,
            school=self.school,
            staff_id="T-001",
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            full_name="Demo Student",
            role=UserRole.STUDENT,
            school=self.school,
        )
        StudentProfile.objects.create(
            user=self.student,
            school=self.school,
            admission_number="ADM-001",
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name="SS2")
        self.class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=self.class_level,
            name="Science A",
        )
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            starts_at="2026-09-01",
            ends_at="2027-07-31",
        )
        self.term = Term.objects.create(
            school=self.school,
            academic_session=self.session,
            name="first",
            starts_at="2026-09-01",
            ends_at="2026-12-15",
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathematics",
            code="MTH",
        )
        self.client = APIClient()

    def enrollment_csv(self):
        return "\n".join(
            [
                "student_email,admission_number,academic_session,term,class_arm",
                f"student@example.com,,{self.session.name},First Term,{self.class_arm}",
            ]
        )

    def teacher_assignment_csv(self):
        return "\n".join(
            [
                "teacher_email,staff_id,class_arm,subject,academic_session,term",
                f"teacher@example.com,,{self.class_arm},Mathematics,{self.session.name},First Term",
            ]
        )

    def test_enrollment_preflight_creates_no_records(self):
        self.client.force_authenticate(self.admin)
        enrollment_count = StudentEnrollment.objects.count()
        batch_count = AcademicImportBatch.objects.count()

        response = self.client.post(
            "/api/academics/imports/preflight/",
            {
                "import_type": "student_enrollments",
                "file": csv_upload("enrollments.csv", self.enrollment_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["can_import"])
        self.assertEqual(response.data["valid_rows"], 1)
        self.assertEqual(StudentEnrollment.objects.count(), enrollment_count)
        self.assertEqual(AcademicImportBatch.objects.count(), batch_count)

    def test_enrollment_import_creates_enrollment(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/academics/imports/",
            {
                "import_type": "student_enrollments",
                "file": csv_upload("enrollments.csv", self.enrollment_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        self.assertTrue(
            StudentEnrollment.objects.filter(
                student=self.student,
                academic_session=self.session,
                term=self.term,
            ).exists()
        )

    def test_teacher_assignment_import_creates_assignment(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/academics/imports/",
            {
                "import_type": "teacher_assignments",
                "file": csv_upload("teacher-assignments.csv", self.teacher_assignment_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        self.assertTrue(
            TeacherClassSubjectAssignment.objects.filter(
                teacher=self.teacher,
                class_arm=self.class_arm,
                subject=self.subject,
                academic_session=self.session,
                term=self.term,
            ).exists()
        )

    def test_missing_student_is_invalid(self):
        self.client.force_authenticate(self.admin)
        content = "\n".join(
            [
                "student_email,admission_number,academic_session,term,class_arm",
                f"missing@example.com,,{self.session.name},First Term,{self.class_arm}",
            ]
        )

        response = self.client.post(
            "/api/academics/imports/preflight/",
            {
                "import_type": "student_enrollments",
                "file": csv_upload("enrollments.csv", content),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_import"])
        self.assertEqual(response.data["summary"]["missing_students"], 1)

    def test_teacher_and_student_are_blocked(self):
        for user in [self.teacher, self.student]:
            self.client.force_authenticate(user)
            response = self.client.post(
                "/api/academics/imports/preflight/",
                {
                    "import_type": "student_enrollments",
                    "file": csv_upload("enrollments.csv", self.enrollment_csv()),
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, 403)

    def test_school_admin_cannot_import_into_another_school(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/academics/imports/preflight/",
            {
                "import_type": "student_enrollments",
                "school": self.other_school.id,
                "file": csv_upload("enrollments.csv", self.enrollment_csv()),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
