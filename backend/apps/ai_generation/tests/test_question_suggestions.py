from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from unittest.mock import patch

from apps.academics.models import ClassLevel, Subject, Topic
from apps.accounts.models import User
from apps.ai_generation.models import (
    AIQuestionSuggestionRun,
    AIQuestionSuggestionStatus,
    AIQuestionSuggestionType,
)
from apps.ai_generation.providers.openai import AIProviderError
from apps.ai_generation.services import apply_question_suggestion
from apps.common.choices import UserRole
from apps.question_bank.models import Question, QuestionOption, QuestionSource
from apps.schools.models import School


class AIQuestionSuggestionTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.other_school = School.objects.create(
            name="Other College",
            slug="other-college",
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
        self.class_level = ClassLevel.objects.create(
            school=self.school,
            name="SS2",
        )
        self.other_class_level = ClassLevel.objects.create(
            school=self.other_school,
            name="SS2",
        )
        self.subject = Subject.objects.create(name="Mathematics", code="MTH")
        self.other_subject = Subject.objects.create(name="Physics", code="PHY")
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
            title="Simultaneous Equations",
        )
        self.mismatched_topic = Topic.objects.create(
            school=self.other_school,
            subject=self.subject,
            class_level=self.other_class_level,
            title="Quadratic Equations",
        )
        self.source = QuestionSource.objects.create(
            name="JAMB Demo",
            source_type="jamb_past_question",
        )
        self.question = self.create_question()
        self.client = APIClient()

    def create_question(self, question_text="What is the sum of roots?"):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            source=self.source,
            question_text=question_text,
            explanation="",
            difficulty="easy",
            status="draft",
            is_active=True,
            created_by=self.teacher,
        )
        for label, text, is_correct in [
            ("A", "2", False),
            ("B", "3", False),
            ("C", "5", True),
            ("D", "6", False),
        ]:
            QuestionOption.objects.create(
                question=question,
                label=label,
                text=text,
                is_correct=is_correct,
            )
        return question

    def ai_payload(self, **overrides):
        payload = {
            "suggested_topic_title": "Simultaneous Equations",
            "suggested_difficulty": "medium",
            "suggested_explanation": "Use the coefficient relationship for roots.",
            "duplicate_warning": "",
            "quality_warning": "",
            "confidence_score": 0.86,
        }
        payload.update(overrides)
        return payload

    @override_settings(AI_GENERATION_ENABLED=True)
    @patch("apps.ai_generation.services.call_openai_for_question_suggestion")
    def test_school_admin_can_request_suggestion_for_own_question(self, mock_call):
        mock_call.return_value = (self.ai_payload(), {"id": "resp_123"})
        self.client.force_authenticate(self.school_admin)

        response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], AIQuestionSuggestionStatus.SUCCEEDED)
        self.assertEqual(response.data["suggested_difficulty"], "medium")
        self.assertEqual(response.data["suggested_topic"], self.other_topic.id)
        self.question.refresh_from_db()
        self.assertEqual(self.question.topic, self.topic)
        self.assertEqual(self.question.explanation, "")

    def test_student_cannot_request_suggestion(self):
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.EXPLANATION_ONLY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_cross_school_question_is_blocked(self):
        self.client.force_authenticate(self.other_school_admin)

        response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.EXPLANATION_ONLY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    @override_settings(AI_GENERATION_ENABLED=True)
    @patch("apps.ai_generation.services.call_openai_for_question_suggestion")
    def test_apply_explanation_and_difficulty(self, mock_call):
        mock_call.return_value = (self.ai_payload(), None)
        self.client.force_authenticate(self.school_admin)
        create_response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION,
            },
            format="json",
        )
        run_id = create_response.data["id"]

        response = self.client.post(
            f"/api/ai-generation/question-suggestions/{run_id}/apply/",
            {"fields_to_apply": ["explanation", "difficulty"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.difficulty, "medium")
        self.assertEqual(
            self.question.explanation,
            "Use the coefficient relationship for roots.",
        )
        self.assertEqual(self.question.topic, self.topic)

    def test_applying_mismatched_topic_is_rejected(self):
        run = AIQuestionSuggestionRun.objects.create(
            school=self.school,
            requested_by=self.school_admin,
            question=self.question,
            suggestion_type=AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION,
            status=AIQuestionSuggestionStatus.SUCCEEDED,
            model_name="test-model",
            suggested_topic=self.mismatched_topic,
        )

        with self.assertRaises(Exception):
            apply_question_suggestion(run, self.school_admin, ["topic"])

    @override_settings(AI_GENERATION_ENABLED=True)
    @patch("apps.ai_generation.services.call_openai_for_question_suggestion")
    def test_invalid_ai_response_marks_run_failed(self, mock_call):
        mock_call.return_value = (
            self.ai_payload(suggested_difficulty="impossible"),
            None,
        )
        self.client.force_authenticate(self.school_admin)

        response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.DIFFICULTY_ONLY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], AIQuestionSuggestionStatus.FAILED)
        self.assertIn("difficulty", response.data["error_message"].lower())

    @override_settings(AI_GENERATION_ENABLED=True)
    @patch("apps.ai_generation.services.call_openai_for_question_suggestion")
    def test_openai_failure_marks_run_failed(self, mock_call):
        mock_call.side_effect = AIProviderError("provider unavailable")
        self.client.force_authenticate(self.school_admin)

        response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.EXPLANATION_ONLY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], AIQuestionSuggestionStatus.FAILED)
        self.assertIn("provider unavailable", response.data["error_message"])

    @override_settings(
        AI_GENERATION_ENABLED=True,
        AI_STORE_RAW_PROVIDER_RESPONSE=False,
    )
    @patch("apps.ai_generation.services.call_openai_for_question_suggestion")
    def test_raw_response_is_not_stored_by_default(self, mock_call):
        mock_call.return_value = (self.ai_payload(), {"id": "resp_123"})
        self.client.force_authenticate(self.school_admin)

        response = self.client.post(
            "/api/ai-generation/question-suggestions/",
            {
                "question": self.question.id,
                "suggestion_type": AIQuestionSuggestionType.TOPIC_DIFFICULTY_EXPLANATION,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["raw_response"])
