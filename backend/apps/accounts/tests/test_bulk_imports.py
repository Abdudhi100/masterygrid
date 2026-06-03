from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import ClassArm, ClassLevel
from apps.accounts.models import StudentProfile, TeacherProfile, User, UserImportBatch
from apps.common.choices import UserRole
from apps.schools.models import School


def csv_upload(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


class UserBulkImportTests(TestCase):
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
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            full_name="Demo Student",
            role=UserRole.STUDENT,
            school=self.school,
        )
        self.class_level = ClassLevel.objects.create(school=self.school, name="SS2")
        self.class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=self.class_level,
            name="Science A",
        )
        self.client = APIClient()

    def student_csv(self, email="new-student@example.com", admission_number="ADM-100"):
        return "\n".join(
            [
                "full_name,email,admission_number,class_arm,guardian_name,guardian_phone,password",
                f"New Student,{email},{admission_number},{self.class_arm},Guardian,08030000001,StrongPass123",
            ]
        )

    def teacher_csv(self, email="new-teacher@example.com", staff_id="T-100"):
        return "\n".join(
            [
                "full_name,email,staff_id,phone_number,password",
                f"New Teacher,{email},{staff_id},08030000002,StrongPass123",
            ]
        )

    def test_student_preflight_valid_csv_creates_no_records(self):
        self.client.force_authenticate(self.admin)
        user_count = User.objects.count()
        batch_count = UserImportBatch.objects.count()

        response = self.client.post(
            "/api/auth/imports/preflight/",
            {
                "import_type": "students",
                "file": csv_upload("students.csv", self.student_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["can_import"])
        self.assertEqual(response.data["valid_rows"], 1)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(UserImportBatch.objects.count(), batch_count)

    def test_student_import_creates_user_and_profile(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/imports/",
            {
                "import_type": "students",
                "file": csv_upload("students.csv", self.student_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        user = User.objects.get(email="new-student@example.com")
        self.assertEqual(user.school, self.school)
        self.assertTrue(
            StudentProfile.objects.filter(user=user, admission_number="ADM-100").exists()
        )

    def test_teacher_import_creates_user_and_profile(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/imports/",
            {
                "import_type": "teachers",
                "file": csv_upload("teachers.csv", self.teacher_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        user = User.objects.get(email="new-teacher@example.com")
        self.assertEqual(user.role, UserRole.TEACHER)
        self.assertTrue(TeacherProfile.objects.filter(user=user, staff_id="T-100").exists())

    def test_duplicate_email_is_detected_and_skipped(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/imports/preflight/",
            {
                "import_type": "students",
                "file": csv_upload(
                    "students.csv",
                    self.student_csv(email="student@example.com", admission_number="ADM-101"),
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["duplicate_rows"], 1)
        self.assertEqual(response.data["summary"]["existing_emails"], 1)

    def test_teacher_and_student_are_blocked(self):
        for user in [self.teacher, self.student]:
            self.client.force_authenticate(user)
            response = self.client.post(
                "/api/auth/imports/preflight/",
                {
                    "import_type": "students",
                    "file": csv_upload("students.csv", self.student_csv()),
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, 403)

    def test_school_admin_cannot_import_into_another_school(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/imports/preflight/",
            {
                "import_type": "students",
                "school": self.other_school.id,
                "file": csv_upload("students.csv", self.student_csv()),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
