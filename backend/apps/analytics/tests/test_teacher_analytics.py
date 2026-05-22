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
from apps.submissions.models import Submission
from apps.submissions.services import create_or_get_submission, submit_assignment


class TeacherAnalyticsTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.other_school = School.objects.create(
            name="Other College",
            slug="other-college",
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
        self.other_school_admin = User.objects.create_user(
            email="other-admin@example.com",
            password="StrongPass123",
            full_name="Other Admin",
            role=UserRole.SCHOOL_ADMIN,
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
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.other_teacher,
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
        self.client = APIClient()

    def create_question(self, text, correct_label="A"):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            question_text=text,
            explanation=f"Explanation for {text}",
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
                is_correct=label == correct_label,
            )
        return question

    def create_published_assignment(self, *, teacher=None, question_count=2):
        for index in range(question_count):
            self.create_question(f"Question {index + 1}")

        assignment = create_assignment_from_topic(
            teacher=teacher or self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=question_count,
            due_at=timezone.now() + timedelta(days=1),
        )
        return publish_assignment(assignment, teacher or self.teacher)

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

    def test_teacher_sees_overview_for_own_assignments(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.teacher)

        response = self.client.get("/api/analytics/teacher/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_assignments_created"], 1)
        self.assertEqual(response.data["graded_submissions"], 1)

    def test_teacher_cannot_see_another_teachers_assignment_analytics(self):
        assignment = self.create_published_assignment(
            teacher=self.other_teacher,
            question_count=1,
        )
        self.client.force_authenticate(self.teacher)

        response = self.client.get(
            f"/api/analytics/teacher/assignments/{assignment.id}/results/"
        )

        self.assertEqual(response.status_code, 404)

    def test_cross_school_analytics_access_is_blocked(self):
        assignment = self.create_published_assignment(question_count=1)
        self.client.force_authenticate(self.other_school_admin)

        response = self.client.get(
            f"/api/analytics/teacher/assignments/{assignment.id}/results/"
        )

        self.assertEqual(response.status_code, 404)

    def test_assignment_result_summary_is_calculated_correctly(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.teacher)

        response = self.client.get(
            f"/api/analytics/teacher/assignments/{assignment.id}/results/"
        )

        self.assertEqual(response.status_code, 200)
        summary = response.data["submission_summary"]
        self.assertEqual(summary["total_students_expected"], 2)
        self.assertEqual(summary["total_graded"], 1)
        self.assertEqual(summary["total_not_started"], 1)
        self.assertEqual(summary["average_percentage"], 50.0)

    def test_weak_student_detection_works(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=0)
        self.client.force_authenticate(self.teacher)

        response = self.client.get("/api/analytics/teacher/weak-students/")

        self.assertEqual(response.status_code, 200)
        student_ids = [item["student_id"] for item in response.data]
        self.assertIn(self.student.id, student_ids)

    def test_weak_topic_detection_works(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=0)
        self.client.force_authenticate(self.teacher)

        response = self.client.get("/api/analytics/teacher/weak-topics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["topic"], self.topic.title)

    def test_question_performance_calculates_correct_and_wrong_counts(self):
        assignment = self.create_published_assignment(question_count=2)
        self.submit_for_student(assignment, self.student, correct_count=1)
        self.client.force_authenticate(self.teacher)

        response = self.client.get(
            f"/api/analytics/teacher/assignments/{assignment.id}/results/"
        )

        performance = response.data["question_performance"]
        self.assertEqual(sum(item["correct_count"] for item in performance), 1)
        self.assertEqual(sum(item["wrong_count"] for item in performance), 1)

    def test_student_cannot_access_teacher_analytics(self):
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/analytics/teacher/overview/")

        self.assertEqual(response.status_code, 403)
