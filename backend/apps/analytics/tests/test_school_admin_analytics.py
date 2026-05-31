from datetime import timedelta

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
from apps.assignments.services import create_assignment_from_topic, publish_assignment
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School
from apps.submissions.services import create_or_get_submission, submit_assignment


class SchoolAdminAnalyticsTests(TestCase):
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
        self.inactive_teacher = User.objects.create_user(
            email="inactive@example.com",
            password="StrongPass123",
            full_name="Inactive Teacher",
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
        self.second_student = User.objects.create_user(
            email="second-student@example.com",
            password="StrongPass123",
            full_name="Second Student",
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
        for student in [self.student, self.second_student]:
            StudentEnrollment.objects.create(
                school=self.school,
                student=student,
                class_arm=self.class_arm,
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

    def create_question(self, text):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            question_text=text,
            difficulty="medium",
            status=QuestionStatus.APPROVED,
            is_active=True,
            created_by=self.teacher,
        )
        for label in ["A", "B", "C", "D"]:
            QuestionOption.objects.create(
                question=question,
                label=label,
                text=f"{text} option {label}",
                is_correct=label == "A",
            )
        return question

    def create_published_assignment(self, question_count=2):
        for index in range(question_count):
            self.create_question(f"Question {index + 1}")

        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=question_count,
            due_at=timezone.now() + timedelta(days=1),
        )
        return publish_assignment(assignment, self.teacher)

    def submit_for_student(self, assignment, student, correct_count):
        submission = create_or_get_submission(student, assignment)
        answers = []
        for index, assignment_question in enumerate(
            assignment.assignment_questions.order_by("order")
        ):
            if index < correct_count:
                selected_option = assignment_question.question.options.get(is_correct=True)
            else:
                selected_option = assignment_question.question.options.filter(
                    is_correct=False
                ).first()
            answers.append(
                {
                    "assignment_question": assignment_question,
                    "selected_option": selected_option,
                }
            )
        return submit_assignment(submission, answers)

    def test_school_admin_sees_only_own_school_analytics(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_students"], 2)
        self.assertEqual(response.data["total_teachers"], 2)

    def test_school_admin_cannot_see_another_schools_data(self):
        self.create_published_assignment(question_count=1)
        self.client.force_authenticate(self.other_admin)

        response = self.client.get("/api/analytics/admin/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_students"], 1)
        self.assertEqual(response.data["total_assignments"], 0)

    def test_teacher_and_student_cannot_access_admin_analytics(self):
        self.client.force_authenticate(self.teacher)
        teacher_response = self.client.get("/api/analytics/admin/overview/")
        self.client.force_authenticate(self.student)
        student_response = self.client.get("/api/analytics/admin/overview/")

        self.assertEqual(teacher_response.status_code, 403)
        self.assertEqual(student_response.status_code, 403)

    def test_class_performance_average_is_correct(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/class-performance/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["average_percentage"], 50.0)
        self.assertEqual(response.data[0]["submission_rate"], 50.0)

    def test_subject_performance_average_is_correct(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/subject-performance/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["average_percentage"], 50.0)

    def test_teacher_activity_status_is_correct(self):
        self.create_published_assignment(question_count=1)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/teacher-activity/")

        statuses = {
            item["teacher_name"]: item["activity_status"]
            for item in response.data
        }
        self.assertEqual(statuses["Inactive Teacher"], "inactive")
        self.assertEqual(statuses["Demo Teacher"], "low_activity")

    def test_assignment_compliance_status_is_correct(self):
        assignment = self.create_published_assignment(question_count=1)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/assignment-compliance/")

        self.assertEqual(response.status_code, 200)
        row = next(
            item for item in response.data if item["assignment_id"] == assignment.id
        )
        self.assertEqual(row["submission_rate"], 50.0)
        self.assertEqual(row["compliance_status"], "warning")

    def test_weak_students_are_detected_correctly(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=0)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/weak-students/")

        self.assertEqual(response.status_code, 200)
        student_ids = [item["student_id"] for item in response.data]
        self.assertIn(self.student.id, student_ids)

    def test_school_admin_intervention_dashboard_detects_risks(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=0)
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/intervention-dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(response.data["overall_risk_level"], ["moderate", "high", "critical"])
        self.assertGreater(response.data["risk_score"], 0)
        self.assertGreaterEqual(
            response.data["summary"]["total_classes_at_risk"],
            1,
        )
        self.assertGreaterEqual(
            response.data["summary"]["total_subjects_at_risk"],
            1,
        )
        self.assertGreaterEqual(
            response.data["summary"]["total_weak_student_clusters"],
            1,
        )
        self.assertTrue(response.data["urgent_interventions"])

        class_card = response.data["class_interventions"][0]
        self.assertEqual(class_card["class_arm_id"], self.class_arm.id)
        self.assertEqual(class_card["action_payload"]["href"], "/admin/analytics/classes")

        subject_card = response.data["subject_interventions"][0]
        self.assertEqual(subject_card["subject_id"], self.subject.id)
        self.assertEqual(
            subject_card["action_payload"]["href"],
            "/admin/analytics/subjects",
        )

    def test_admin_intervention_dashboard_has_safe_empty_state(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/analytics/admin/intervention-dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["risk_score"], 0)
        self.assertEqual(response.data["overall_risk_level"], "low")
        self.assertEqual(response.data["urgent_interventions"], [])
        self.assertEqual(response.data["class_interventions"], [])

    def test_teacher_and_student_cannot_access_admin_intervention_dashboard(self):
        self.client.force_authenticate(self.teacher)
        teacher_response = self.client.get(
            "/api/analytics/admin/intervention-dashboard/",
        )
        self.client.force_authenticate(self.student)
        student_response = self.client.get(
            "/api/analytics/admin/intervention-dashboard/",
        )

        self.assertEqual(teacher_response.status_code, 403)
        self.assertEqual(student_response.status_code, 403)
