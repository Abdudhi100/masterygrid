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
from apps.interventions.models import StudentIntervention
from apps.notifications.models import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.services import create_notification
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School
from apps.submissions.services import create_or_get_submission, submit_assignment


class NotificationApiTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
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
        self.other_student = User.objects.create_user(
            email="other-student@example.com",
            password="StrongPass123",
            full_name="Other Student",
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
            title="Quadratics",
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

    def create_question(self, index):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            question_text=f"E2E notification question {index}",
            difficulty="medium",
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
        return question

    def create_assignment(self):
        for index in range(1, 6):
            self.create_question(index)
        return create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Notification Assignment",
            question_count=5,
            due_at=timezone.now() + timedelta(days=2),
        )

    def test_notification_creation_defaults_school(self):
        notification = create_notification(
            recipient=self.student,
            actor=self.teacher,
            title="Test notification",
            message="Hello",
        )

        self.assertEqual(notification.school, self.school)
        self.assertEqual(notification.status, NotificationStatus.UNREAD)

    def test_user_sees_only_own_notifications(self):
        create_notification(recipient=self.student, title="Mine")
        create_notification(recipient=self.other_student, title="Other")
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Mine")

    def test_unread_count_and_mark_read_unread_archive(self):
        notification = create_notification(recipient=self.student, title="Read me")
        self.client.force_authenticate(self.student)

        count_response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(count_response.data["unread_count"], 1)

        read_response = self.client.post(
            f"/api/notifications/{notification.id}/mark-read/",
        )
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.data["status"], NotificationStatus.READ)
        self.assertIsNotNone(read_response.data["read_at"])

        unread_response = self.client.post(
            f"/api/notifications/{notification.id}/mark-unread/",
        )
        self.assertEqual(unread_response.status_code, 200)
        self.assertEqual(unread_response.data["status"], NotificationStatus.UNREAD)
        self.assertIsNone(unread_response.data["read_at"])

        archive_response = self.client.post(
            f"/api/notifications/{notification.id}/archive/",
        )
        self.assertEqual(archive_response.status_code, 200)
        self.assertEqual(archive_response.data["status"], NotificationStatus.ARCHIVED)

    def test_cross_user_access_blocked(self):
        notification = create_notification(recipient=self.student, title="Private")
        self.client.force_authenticate(self.other_student)

        response = self.client.get(f"/api/notifications/{notification.id}/")

        self.assertEqual(response.status_code, 404)

    def test_assignment_publish_creates_student_notification(self):
        assignment = self.create_assignment()

        publish_assignment(assignment, self.teacher)

        notification = Notification.objects.get(recipient=self.student)
        self.assertEqual(
            notification.notification_type,
            NotificationType.ASSIGNMENT_PUBLISHED,
        )
        self.assertEqual(notification.target_url, f"/student/assignments/{assignment.id}")

    def test_assignment_submission_creates_teacher_notification(self):
        assignment = publish_assignment(self.create_assignment(), self.teacher)
        Notification.objects.all().delete()
        submission = create_or_get_submission(self.student, assignment)
        answers = []
        for assignment_question in assignment.assignment_questions.order_by("order"):
            answers.append(
                {
                    "assignment_question": assignment_question,
                    "selected_option": assignment_question.question.options.get(
                        is_correct=True,
                    ),
                }
            )

        graded_submission = submit_assignment(submission, answers)

        notification = Notification.objects.get(recipient=self.teacher)
        self.assertEqual(
            notification.notification_type,
            NotificationType.ASSIGNMENT_SUBMITTED,
        )
        self.assertEqual(
            notification.target_url,
            f"/teacher/assignments/{assignment.id}/results",
        )
        self.assertEqual(notification.metadata["submission_id"], graded_submission.id)

    def test_intervention_created_creates_notification(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/interventions/",
            {
                "student": self.student.id,
                "assigned_to": self.teacher.id,
                "title": "Parent meeting required",
                "description": "Schedule a follow-up meeting.",
                "priority": "high",
                "category": "parent_contact",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        notification = Notification.objects.get(recipient=self.teacher)
        self.assertEqual(
            notification.notification_type,
            NotificationType.INTERVENTION_CREATED,
        )
        self.assertEqual(
            notification.target_url,
            f"/teacher/interventions/{response.data['id']}",
        )

    def test_intervention_note_creates_notification(self):
        intervention = StudentIntervention.objects.create(
            school=self.school,
            student=self.student,
            created_by=self.admin,
            assigned_to=self.teacher,
            title="Revision follow-up",
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            f"/api/interventions/{intervention.id}/add-note/",
            {"note": "Parent confirmed the revision schedule."},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        notification = Notification.objects.get(recipient=self.teacher)
        self.assertEqual(
            notification.notification_type,
            NotificationType.INTERVENTION_NOTE_ADDED,
        )
        self.assertEqual(notification.object_id, str(response.data["id"]))
