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
from apps.notifications.models import NotificationPriority, NotificationType
from apps.notifications.services import create_notification
from apps.practice.models import PracticeSession, PracticeSessionStatus
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School
from apps.submissions.services import create_or_get_submission, submit_assignment


class StudentDashboardAnalyticsTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123",
            full_name="Demo Teacher",
            role=UserRole.TEACHER,
            school=self.school,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123",
            full_name="Demo Admin",
            role=UserRole.SCHOOL_ADMIN,
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

    def create_published_assignment(self, title, due_at):
        self.create_question(title)
        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title=title,
            question_count=1,
            due_at=due_at,
        )
        return publish_assignment(assignment, self.teacher)

    def submit_for_student(self, assignment, correct=True):
        submission = create_or_get_submission(self.student, assignment)
        assignment_question = assignment.assignment_questions.order_by("order").first()
        selected_option = assignment_question.question.options.get(
            is_correct=correct,
        )
        return submit_assignment(
            submission,
            [
                {
                    "assignment_question": assignment_question,
                    "selected_option": selected_option,
                }
            ],
        )

    def create_submitted_practice_session(self):
        return PracticeSession.objects.create(
            school=self.school,
            student=self.student,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            class_arm=self.class_arm,
            difficulty="mixed",
            question_count_requested=2,
            status=PracticeSessionStatus.SUBMITTED,
            score=1,
            total_marks=2,
            percentage=50,
            submitted_at=timezone.now(),
        )

    def test_student_dashboard_composes_assignments_practice_learning_and_notifications(self):
        now = timezone.now()
        due_soon = self.create_published_assignment(
            "Due Soon Assignment",
            now + timedelta(hours=2),
        )
        overdue = self.create_published_assignment(
            "Overdue Assignment",
            now - timedelta(hours=2),
        )
        graded = self.create_published_assignment(
            "Graded Assignment",
            now + timedelta(days=2),
        )
        self.submit_for_student(graded, correct=True)
        self.create_submitted_practice_session()
        create_notification(
            recipient=self.student,
            actor=self.teacher,
            title="Unique dashboard notification",
            message="Check your dashboard.",
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.HIGH,
            target_url="/student/practice",
        )

        self.client.force_authenticate(self.student)
        response = self.client.get("/api/analytics/student/dashboard/")

        self.assertEqual(response.status_code, 200)
        summary = response.data["summary"]
        self.assertEqual(summary["pending_assignments_count"], 2)
        self.assertEqual(summary["due_soon_assignments_count"], 1)
        self.assertEqual(summary["overdue_assignments_count"], 1)
        self.assertEqual(summary["graded_assignments_count"], 1)
        self.assertEqual(summary["assignment_average"], 100.0)
        self.assertEqual(summary["practice_sessions_count"], 1)
        self.assertEqual(summary["practice_average"], 50.0)
        self.assertGreaterEqual(summary["unread_notifications_count"], 1)

        due_soon_titles = [
            item["title"] for item in response.data["assignments"]["due_soon"]
        ]
        overdue_titles = [
            item["title"] for item in response.data["assignments"]["overdue"]
        ]
        recent_titles = [
            item["assignment_title"]
            for item in response.data["assignments"]["recently_graded"]
        ]
        self.assertIn(due_soon.title, due_soon_titles)
        self.assertIn(overdue.title, overdue_titles)
        self.assertIn(graded.title, recent_titles)
        self.assertEqual(response.data["learning_path"]["top_topic_card"]["topic_id"], self.topic.id)
        self.assertTrue(response.data["practice"]["recent_sessions"])
        self.assertEqual(
            response.data["notifications"][0]["title"],
            "Unique dashboard notification",
        )
        self.assertTrue(response.data["quick_actions"])
        self.assertNotIn("correct_option", str(response.data))
        self.assertNotIn("Explanation for", str(response.data))

    def test_only_students_can_access_student_dashboard(self):
        self.client.force_authenticate(self.teacher)
        teacher_response = self.client.get("/api/analytics/student/dashboard/")

        self.client.force_authenticate(self.admin)
        admin_response = self.client.get("/api/analytics/student/dashboard/")

        self.client.force_authenticate(None)
        anonymous_response = self.client.get("/api/analytics/student/dashboard/")

        self.assertEqual(teacher_response.status_code, 403)
        self.assertEqual(admin_response.status_code, 403)
        self.assertIn(anonymous_response.status_code, [401, 403])
