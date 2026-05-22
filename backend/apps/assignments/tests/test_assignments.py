from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import (
    ClassArm,
    ClassLevel,
    Subject,
    TeacherClassSubjectAssignment,
    Topic,
)
from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.assignments.services import create_assignment_from_topic
from apps.common.choices import AssignmentStatus, QuestionStatus, UserRole
from apps.question_bank.models import Question
from apps.schools.models import School


class AssignmentEngineTests(TestCase):
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
        self.school_admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123",
            full_name="Demo Admin",
            role=UserRole.SCHOOL_ADMIN,
            school=self.school,
        )
        self.other_school_admin = User.objects.create_user(
            email="other-admin@example.com",
            password="StrongPass123",
            full_name="Other Admin",
            role=UserRole.SCHOOL_ADMIN,
            school=self.other_school,
        )
        self.class_level = ClassLevel.objects.create(
            school=self.school,
            name="SS2",
        )
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
        self.other_topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Linear Equations",
        )
        self.client = APIClient()

    def assign_teacher(self, teacher=None):
        return TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=teacher or self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
        )

    def create_question(self, *, topic=None, status=QuestionStatus.APPROVED, school=None):
        return Question.objects.create(
            school=school,
            subject=self.subject,
            topic=topic or self.topic,
            class_level=self.class_level,
            question_text=f"What is tested in {topic or self.topic}?",
            difficulty="medium",
            status=status,
            is_active=status != QuestionStatus.ARCHIVED,
            created_by=self.teacher,
        )

    def test_teacher_cannot_create_assignment_without_class_subject_assignment(self):
        self.create_question()

        with self.assertRaises(ValidationError):
            create_assignment_from_topic(
                teacher=self.teacher,
                class_arm=self.class_arm,
                subject=self.subject,
                topic=self.topic,
                title="Quadratic Practice",
                question_count=1,
            )

    def test_assignment_generation_fails_if_not_enough_approved_questions(self):
        self.assign_teacher()
        self.create_question(status=QuestionStatus.DRAFT)

        with self.assertRaises(ValidationError):
            create_assignment_from_topic(
                teacher=self.teacher,
                class_arm=self.class_arm,
                subject=self.subject,
                topic=self.topic,
                title="Quadratic Practice",
                question_count=1,
            )

    def test_draft_rejected_and_archived_questions_are_excluded(self):
        self.assign_teacher()
        self.create_question(status=QuestionStatus.APPROVED)
        self.create_question(status=QuestionStatus.DRAFT)
        self.create_question(status=QuestionStatus.REJECTED)
        self.create_question(status=QuestionStatus.ARCHIVED)

        with self.assertRaises(ValidationError):
            create_assignment_from_topic(
                teacher=self.teacher,
                class_arm=self.class_arm,
                subject=self.subject,
                topic=self.topic,
                title="Quadratic Practice",
                question_count=2,
            )

    def test_generated_assignment_contains_only_matching_topic_questions(self):
        self.assign_teacher()
        matching_question = self.create_question(topic=self.topic)
        self.create_question(topic=self.other_topic)

        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=1,
        )

        selected_questions = [item.question for item in assignment.assignment_questions.all()]
        self.assertEqual(selected_questions, [matching_question])

    def test_published_at_is_set_on_publish(self):
        self.assign_teacher()
        self.create_question()
        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=1,
        )
        self.client.force_authenticate(self.teacher)

        response = self.client.post(f"/api/assignments/{assignment.id}/publish/")
        assignment.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(assignment.status, AssignmentStatus.PUBLISHED)
        self.assertIsNotNone(assignment.published_at)

    def test_teacher_cannot_publish_another_teachers_assignment(self):
        self.assign_teacher(teacher=self.other_teacher)
        self.create_question()
        assignment = create_assignment_from_topic(
            teacher=self.other_teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Other Teacher Practice",
            question_count=1,
        )
        self.client.force_authenticate(self.teacher)

        response = self.client.post(f"/api/assignments/{assignment.id}/publish/")

        self.assertIn(response.status_code, [403, 404])

    def test_school_admin_can_view_school_assignments(self):
        self.assign_teacher()
        self.create_question()
        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=1,
        )
        self.client.force_authenticate(self.school_admin)

        response = self.client.get(f"/api/assignments/{assignment.id}/")

        self.assertEqual(response.status_code, 200)

    def test_another_school_cannot_access_assignment(self):
        self.assign_teacher()
        self.create_question()
        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=1,
        )
        self.client.force_authenticate(self.other_school_admin)

        response = self.client.get(f"/api/assignments/{assignment.id}/")

        self.assertEqual(response.status_code, 404)

    def test_generate_from_topic_endpoint_creates_draft_assignment(self):
        self.assign_teacher()
        self.create_question()
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            "/api/assignments/generate-from-topic/",
            {
                "class_arm": self.class_arm.id,
                "subject": self.subject.id,
                "topic": self.topic.id,
                "title": "Quadratic Practice",
                "question_count": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        assignment = Assignment.objects.get(id=response.data["id"])
        self.assertEqual(assignment.status, AssignmentStatus.DRAFT)
        self.assertEqual(assignment.assignment_questions.count(), 1)
