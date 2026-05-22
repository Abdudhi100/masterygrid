from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import ClassLevel, Subject, Topic
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question, QuestionSource
from apps.question_bank.services import approve_question, get_approved_questions_for_topic
from apps.schools.models import School


class QuestionBankTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123",
            full_name="Demo Teacher",
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
        self.class_level = ClassLevel.objects.create(
            school=self.school,
            name="SS2",
        )
        self.subject = Subject.objects.create(name="Mathematics", code="MTH")
        self.topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Quadratic Equations",
        )
        self.source = QuestionSource.objects.create(
            name="Teacher Created",
            source_type="teacher_created",
        )
        self.client = APIClient()

    def payload(self, **overrides):
        data = {
            "subject": self.subject.id,
            "topic": self.topic.id,
            "class_level": self.class_level.id,
            "source": self.source.id,
            "question_text": "What is the sum of roots of x^2 - 5x + 6 = 0?",
            "difficulty": "medium",
            "options": [
                {"label": "A", "text": "2", "is_correct": False},
                {"label": "B", "text": "3", "is_correct": False},
                {"label": "C", "text": "5", "is_correct": True},
                {"label": "D", "text": "6", "is_correct": False},
            ],
        }
        data.update(overrides)
        return data

    def test_cannot_create_question_without_four_options(self):
        self.client.force_authenticate(self.teacher)
        data = self.payload(options=self.payload()["options"][:3])

        response = self.client.post("/api/question-bank/questions/", data, format="json")

        self.assertEqual(response.status_code, 400)

    def test_cannot_create_question_with_two_correct_options(self):
        self.client.force_authenticate(self.teacher)
        data = self.payload(
            options=[
                {"label": "A", "text": "2", "is_correct": True},
                {"label": "B", "text": "3", "is_correct": False},
                {"label": "C", "text": "5", "is_correct": True},
                {"label": "D", "text": "6", "is_correct": False},
            ]
        )

        response = self.client.post("/api/question-bank/questions/", data, format="json")

        self.assertEqual(response.status_code, 400)

    def test_cannot_create_question_with_topic_subject_mismatch(self):
        other_subject = Subject.objects.create(name="Physics", code="PHY")
        self.client.force_authenticate(self.teacher)
        data = self.payload(subject=other_subject.id)

        response = self.client.post("/api/question-bank/questions/", data, format="json")

        self.assertEqual(response.status_code, 400)

    def test_teacher_created_question_is_forced_to_draft(self):
        self.client.force_authenticate(self.teacher)
        data = self.payload(status=QuestionStatus.DRAFT)

        response = self.client.post("/api/question-bank/questions/", data, format="json")

        self.assertEqual(response.status_code, 201)
        question = Question.objects.get(id=response.data["id"])
        self.assertEqual(question.status, QuestionStatus.DRAFT)
        self.assertEqual(question.school, self.school)
        self.assertEqual(question.created_by, self.teacher)

    def test_school_admin_approves_school_question(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post(
            "/api/question-bank/questions/",
            self.payload(),
            format="json",
        )
        question = Question.objects.get(id=response.data["id"])

        approved_question = approve_question(question, self.school_admin)

        self.assertEqual(approved_question.status, QuestionStatus.APPROVED)
        self.assertEqual(approved_question.reviewed_by, self.school_admin)

    def test_non_approved_questions_are_excluded_from_topic_query(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post(
            "/api/question-bank/questions/",
            self.payload(),
            format="json",
        )
        question = Question.objects.get(id=response.data["id"])

        questions = get_approved_questions_for_topic(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
        )
        self.assertNotIn(question, questions)

        approve_question(question, self.school_admin)
        questions = get_approved_questions_for_topic(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
        )
        self.assertIn(question, questions)
