from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import StudentProfile, TeacherProfile, User
from apps.common.choices import UserRole
from apps.schools.models import School


class SchoolUserManagementTests(TestCase):
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
        self.other_teacher = User.objects.create_user(
            email="other-teacher@example.com",
            password="StrongPass123",
            full_name="Other Teacher",
            role=UserRole.TEACHER,
            school=self.other_school,
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123",
            full_name="Demo Student",
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
        self.client = APIClient()

    def test_school_admin_lists_only_own_teachers(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/auth/teachers/")

        self.assertEqual(response.status_code, 200)
        teacher_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.teacher.id, teacher_ids)
        self.assertNotIn(self.other_teacher.id, teacher_ids)

    def test_school_admin_lists_only_own_students(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/auth/students/")

        self.assertEqual(response.status_code, 200)
        student_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.student.id, student_ids)
        self.assertNotIn(self.other_student.id, student_ids)

    def test_teacher_cannot_access_teacher_list(self):
        self.client.force_authenticate(self.teacher)

        response = self.client.get("/api/auth/teachers/")

        self.assertEqual(response.status_code, 403)

    def test_school_admin_creates_teacher_profile_for_own_school_teacher(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/teacher-profiles/",
            {
                "user": self.teacher.id,
                "school": self.school.id,
                "staff_id": "T-001",
                "phone_number": "08030000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            TeacherProfile.objects.filter(user=self.teacher, staff_id="T-001").exists()
        )

    def test_school_admin_cannot_create_cross_school_teacher_profile(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/teacher-profiles/",
            {
                "user": self.other_teacher.id,
                "school": self.other_school.id,
                "staff_id": "T-999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_school_admin_creates_student_profile_for_own_school_student(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/student-profiles/",
            {
                "user": self.student.id,
                "school": self.school.id,
                "admission_number": "ADM-001",
                "guardian_name": "Guardian",
                "guardian_phone": "08030000001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            StudentProfile.objects.filter(
                user=self.student,
                admission_number="ADM-001",
            ).exists()
        )

    def test_teacher_can_view_own_profile(self):
        profile = TeacherProfile.objects.create(
            user=self.teacher,
            school=self.school,
            staff_id="T-002",
        )
        self.client.force_authenticate(self.teacher)

        response = self.client.get(f"/api/auth/teacher-profiles/{profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], profile.id)

    def test_student_can_view_own_profile(self):
        profile = StudentProfile.objects.create(
            user=self.student,
            school=self.school,
            admission_number="ADM-002",
        )
        self.client.force_authenticate(self.student)

        response = self.client.get(f"/api/auth/student-profiles/{profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], profile.id)

    def test_register_teacher_with_profile_data_creates_teacher_profile(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new-teacher@example.com",
                "password": "StrongPass123",
                "full_name": "New Teacher",
                "role": UserRole.TEACHER,
                "school": self.school.id,
                "staff_id": "T-003",
                "phone_number": "08030000002",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new-teacher@example.com")
        self.assertTrue(TeacherProfile.objects.filter(user=user).exists())

    def test_register_student_with_profile_data_creates_student_profile(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new-student@example.com",
                "password": "StrongPass123",
                "full_name": "New Student",
                "role": UserRole.STUDENT,
                "school": self.school.id,
                "admission_number": "ADM-003",
                "guardian_name": "Guardian",
                "guardian_phone": "08030000003",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new-student@example.com")
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())
