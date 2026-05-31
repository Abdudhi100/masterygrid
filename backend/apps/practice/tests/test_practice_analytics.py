from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import ClassLevel, Subject, Topic
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.practice.models import (
    PracticeAnswer,
    PracticeSession,
    PracticeSessionQuestion,
    PracticeSessionStatus,
)
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School


class PracticeAnalyticsTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Demo College", slug="demo-college")
        self.other_school = School.objects.create(
            name="Other College",
            slug="other-college",
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
        self.physics = Subject.objects.create(name="Physics", code="PHY")
        self.weak_topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Quadratic Equations",
        )
        self.strong_topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Logarithms",
        )
        self.average_topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Simultaneous Equations",
        )
        self.unpracticed_topic = Topic.objects.create(
            school=self.school,
            subject=self.physics,
            class_level=self.class_level,
            title="Motion",
        )
        self.no_question_topic = Topic.objects.create(
            school=self.school,
            subject=self.physics,
            class_level=self.class_level,
            title="Waves",
        )
        self.global_topic = Topic.objects.create(
            subject=self.subject,
            class_level=self.class_level,
            title="Global Geometry",
        )
        self.client = APIClient()

    def create_question(self, topic, text, *, school=None, subject=None):
        question = Question.objects.create(
            school=self.school if school is None else school,
            subject=subject or topic.subject,
            topic=topic,
            class_level=self.class_level,
            question_text=text,
            explanation=f"Explanation for {text}",
            difficulty="medium",
            status=QuestionStatus.APPROVED,
            is_active=True,
            created_by=self.teacher,
        )
        options = {}
        for label in ["A", "B", "C", "D"]:
            options[label] = QuestionOption.objects.create(
                question=question,
                label=label,
                text=f"{text} option {label}",
                is_correct=label == "A",
            )
        return question, options

    def create_submitted_session(
        self,
        *,
        student=None,
        topic=None,
        subject=None,
        correct_count=0,
        total_questions=5,
        status=PracticeSessionStatus.SUBMITTED,
    ):
        topic = topic or self.weak_topic
        subject = subject or topic.subject
        student = student or self.student
        score = correct_count if status == PracticeSessionStatus.SUBMITTED else 0
        total_marks = total_questions if status == PracticeSessionStatus.SUBMITTED else 0
        percentage = (
            Decimal(score) / Decimal(total_marks) * Decimal("100")
            if total_marks
            else None
        )
        session = PracticeSession.objects.create(
            school=student.school,
            student=student,
            subject=subject,
            topic=topic,
            class_level=self.class_level,
            difficulty="mixed",
            question_count_requested=total_questions,
            status=status,
            score=score,
            total_marks=total_marks,
            percentage=percentage,
            started_at=timezone.now(),
            submitted_at=timezone.now()
            if status == PracticeSessionStatus.SUBMITTED
            else None,
        )
        for index in range(total_questions):
            question, options = self.create_question(
                topic,
                f"{topic.title} question {session.id}-{index}",
            )
            session_question = PracticeSessionQuestion.objects.create(
                session=session,
                question=question,
                order=index + 1,
                marks=1,
                question_text=question.question_text,
                explanation=question.explanation,
                options_snapshot=[
                    {
                        "id": option.id,
                        "label": option.label,
                        "text": option.text,
                        "is_correct": option.is_correct,
                    }
                    for option in options.values()
                ],
            )
            is_correct = index < correct_count
            selected_option = options["A"] if is_correct else options["B"]
            if status == PracticeSessionStatus.SUBMITTED:
                PracticeAnswer.objects.create(
                    session=session,
                    session_question=session_question,
                    selected_option=selected_option,
                    selected_label=selected_option.label,
                    is_correct=is_correct,
                    marks_awarded=1 if is_correct else 0,
                    answered_at=timezone.now(),
                )
        return session

    def test_student_can_access_own_analytics(self):
        self.create_submitted_session(correct_count=3, total_questions=5)
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_sessions_completed"], 1)

    def test_teacher_admin_and_anonymous_are_blocked(self):
        self.client.force_authenticate(self.teacher)
        teacher_response = self.client.get("/api/practice/analytics/dashboard/")

        self.client.force_authenticate(self.school_admin)
        admin_response = self.client.get("/api/practice/analytics/dashboard/")

        self.client.force_authenticate(user=None)
        anonymous_response = self.client.get("/api/practice/analytics/dashboard/")

        self.assertEqual(teacher_response.status_code, 403)
        self.assertEqual(admin_response.status_code, 403)
        self.assertIn(anonymous_response.status_code, [401, 403])

    def test_no_history_returns_safe_dashboard_with_recommendations(self):
        self.create_question(self.unpracticed_topic, "Available motion question")
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_sessions_completed"], 0)
        self.assertIsNone(response.data["summary"]["overall_average_percentage"])
        self.assertEqual(response.data["subject_performance"], [])
        self.assertEqual(response.data["topic_performance"], [])
        self.assertIn("Complete a practice session", response.data["message"])
        self.assertEqual(response.data["recommendations"][0]["priority"], "low")

    def test_submitted_sessions_count_and_in_progress_excluded(self):
        self.create_submitted_session(correct_count=3, total_questions=5)
        self.create_submitted_session(
            correct_count=5,
            total_questions=5,
            status=PracticeSessionStatus.IN_PROGRESS,
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_sessions_completed"], 1)
        self.assertEqual(response.data["total_questions_answered"], 5)

    def test_weighted_average_is_computed_correctly(self):
        self.create_submitted_session(correct_count=1, total_questions=2)
        self.create_submitted_session(correct_count=2, total_questions=8)
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overall_average_percentage"], 30.0)

    def test_weak_and_strong_topics_detected_correctly(self):
        self.create_submitted_session(
            topic=self.weak_topic,
            correct_count=2,
            total_questions=5,
        )
        self.create_submitted_session(
            topic=self.strong_topic,
            correct_count=4,
            total_questions=5,
        )
        self.client.force_authenticate(self.student)

        weak_response = self.client.get("/api/practice/analytics/weak-topics/")
        strong_response = self.client.get("/api/practice/analytics/strong-topics/")

        self.assertEqual(weak_response.status_code, 200)
        self.assertEqual(strong_response.status_code, 200)
        self.assertEqual(weak_response.data[0]["topic_id"], self.weak_topic.id)
        self.assertEqual(strong_response.data[0]["topic_id"], self.strong_topic.id)

    def test_recommendations_prioritize_weak_topics(self):
        self.create_submitted_session(
            topic=self.weak_topic,
            correct_count=1,
            total_questions=5,
        )
        self.create_submitted_session(
            topic=self.average_topic,
            correct_count=3,
            total_questions=5,
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/recommendations/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["topic_id"], self.weak_topic.id)
        self.assertEqual(response.data[0]["priority"], "high")
        self.assertEqual(response.data[0]["recommended_difficulty"], "easy")

    def test_recommendations_exclude_topics_with_no_approved_questions(self):
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/recommendations/")

        topic_ids = {item["topic_id"] for item in response.data}
        self.assertNotIn(self.no_question_topic.id, topic_ids)

    def test_global_question_availability_can_drive_recommendations(self):
        self.create_question(
            self.global_topic,
            "Global geometry question",
            school=None,
            subject=self.subject,
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/recommendations/")

        topic_ids = {item["topic_id"] for item in response.data}
        self.assertIn(self.global_topic.id, topic_ids)

    def test_cross_student_data_is_excluded(self):
        self.create_submitted_session(
            student=self.other_student,
            correct_count=5,
            total_questions=5,
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/analytics/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_sessions_completed"], 0)

    def test_learning_path_prioritizes_weak_topics(self):
        self.create_submitted_session(
            topic=self.weak_topic,
            correct_count=1,
            total_questions=5,
        )
        self.create_submitted_session(
            topic=self.average_topic,
            correct_count=3,
            total_questions=5,
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/learning-path/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overall_status"], "needs_attention")
        self.assertEqual(
            response.data["recommended_next_action"]["topic_id"],
            self.weak_topic.id,
        )
        self.assertEqual(
            response.data["recommended_next_action"]["category"],
            "weak_topic",
        )
        self.assertEqual(
            response.data["recommended_next_action"]["action_payload"]["subject"],
            self.subject.id,
        )
        self.assertEqual(
            response.data["recommended_next_action"]["action_payload"]["topic"],
            self.weak_topic.id,
        )
        self.assertGreaterEqual(len(response.data["topic_cards"]), 2)

    def test_learning_path_handles_no_history_with_available_questions(self):
        self.create_question(self.unpracticed_topic, "Available motion question")
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/learning-path/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overall_status"], "getting_started")
        self.assertEqual(
            response.data["recommended_next_action"]["category"],
            "new_topic",
        )
        self.assertEqual(response.data["summary"]["total_sessions_completed"], 0)
        self.assertEqual(
            response.data["recommended_next_action"]["available_question_count"],
            1,
        )

    def test_learning_path_returns_empty_state_when_no_questions_exist(self):
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/practice/learning-path/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["overall_status"], "no_questions_available")
        self.assertIsNone(response.data["recommended_next_action"])
        self.assertEqual(response.data["topic_cards"], [])
