from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import ClassLevel, Subject, Topic
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.practice.models import PracticeSession, PracticeSessionStatus
from apps.question_bank.models import Question, QuestionOption
from apps.schools.models import School


class PracticeWorkflowTests(TestCase):
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
        self.class_level = ClassLevel.objects.create(
            school=self.school,
            name="SS2",
        )
        self.other_class_level = ClassLevel.objects.create(
            school=self.other_school,
            name="SS2",
        )
        self.subject = Subject.objects.create(name="Mathematics", code="MTH")
        self.topic = Topic.objects.create(
            school=self.school,
            subject=self.subject,
            class_level=self.class_level,
            title="Quadratic Equations",
        )
        self.other_topic = Topic.objects.create(
            school=self.other_school,
            subject=self.subject,
            class_level=self.other_class_level,
            title="Quadratic Equations",
        )
        self.client = APIClient()

    def create_question(
        self,
        text,
        *,
        school=None,
        topic=None,
        class_level=None,
        difficulty="medium",
        status=QuestionStatus.APPROVED,
        is_active=True,
        correct_label="A",
    ):
        question = Question.objects.create(
            school=self.school if school is None else school,
            subject=self.subject,
            topic=topic or self.topic,
            class_level=class_level or self.class_level,
            question_text=text,
            explanation=f"Explanation for {text}",
            difficulty=difficulty,
            status=status,
            is_active=is_active,
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

    def start_payload(self, **overrides):
        payload = {
            "subject": self.subject.id,
            "topic": self.topic.id,
            "difficulty": "mixed",
            "question_count": 1,
        }
        payload.update(overrides)
        return payload

    def start_practice(self, **overrides):
        self.client.force_authenticate(self.student)
        return self.client.post(
            "/api/practice/sessions/start/",
            self.start_payload(**overrides),
            format="json",
        )

    def test_student_can_start_practice(self):
        self.create_question("Approved practice question")

        response = self.start_practice()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], PracticeSessionStatus.IN_PROGRESS)
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(len(response.data["questions"][0]["options"]), 4)

    def test_teacher_cannot_start_practice(self):
        self.create_question("Approved practice question")
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            "/api/practice/sessions/start/",
            self.start_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_is_blocked(self):
        self.create_question("Approved practice question")

        response = self.client.post(
            "/api/practice/sessions/start/",
            self.start_payload(),
            format="json",
        )

        self.assertIn(response.status_code, [401, 403])

    def test_only_approved_active_questions_are_selected(self):
        approved = self.create_question("Approved active")
        self.create_question("Draft question", status=QuestionStatus.DRAFT)
        self.create_question("Rejected question", status=QuestionStatus.REJECTED)
        self.create_question("Archived question", status=QuestionStatus.ARCHIVED)
        self.create_question("Inactive question", is_active=False)

        response = self.start_practice()

        self.assertEqual(response.status_code, 201)
        session = PracticeSession.objects.get(id=response.data["id"])
        selected_ids = list(session.session_questions.values_list("question_id", flat=True))
        self.assertEqual(selected_ids, [approved.id])

    def test_cross_school_questions_are_excluded(self):
        self.create_question(
            "Other school approved",
            school=self.other_school,
            topic=self.other_topic,
            class_level=self.other_class_level,
        )

        response = self.start_practice()

        self.assertEqual(response.status_code, 400)
        self.assertIn("Only 0 approved active question", str(response.data))

    def test_insufficient_questions_returns_clear_error(self):
        self.create_question("Only one approved question")

        response = self.start_practice(question_count=2)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Only 1 approved active question", str(response.data))

    def test_correct_answers_are_hidden_before_submit(self):
        self.create_question("Hidden answer question")

        response = self.start_practice()

        self.assertEqual(response.status_code, 201)
        response_text = str(response.data)
        self.assertNotIn("is_correct", response_text)
        self.assertNotIn("correct_option", response_text)
        self.assertNotIn("Explanation for", response_text)

    def test_submit_grades_correctly(self):
        self.create_question("Correct answer question", correct_label="A")
        self.create_question("Wrong answer question", correct_label="B")
        start_response = self.start_practice(question_count=2)
        session = PracticeSession.objects.get(id=start_response.data["id"])

        answers = []
        for session_question in session.session_questions.select_related("question"):
            selected_label = "A"
            selected_option = session_question.question.options.get(label=selected_label)
            answers.append(
                {
                    "session_question": session_question.id,
                    "selected_option": selected_option.id,
                }
            )

        response = self.client.post(
            f"/api/practice/sessions/{session.id}/submit/",
            {"answers": answers},
            format="json",
        )
        session.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.status, PracticeSessionStatus.SUBMITTED)
        self.assertEqual(session.score, 1)
        self.assertEqual(session.total_marks, 2)
        self.assertEqual(session.percentage, Decimal("50.00"))
        self.assertEqual(len(response.data["answers"]), 2)
        self.assertIn("correct_option", response.data["answers"][0])
        self.assertIn("explanation", response.data["answers"][0])

    def test_duplicate_submit_is_blocked(self):
        self.create_question("Duplicate submit question")
        start_response = self.start_practice()
        session = PracticeSession.objects.get(id=start_response.data["id"])
        session_question = session.session_questions.select_related("question").get()
        selected_option = session_question.question.options.get(label="A")
        payload = {
            "answers": [
                {
                    "session_question": session_question.id,
                    "selected_option": selected_option.id,
                }
            ]
        }
        self.client.post(
            f"/api/practice/sessions/{session.id}/submit/",
            payload,
            format="json",
        )

        response = self.client.post(
            f"/api/practice/sessions/{session.id}/submit/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_student_cannot_access_another_students_session(self):
        self.create_question("Private practice question")
        start_response = self.start_practice()
        self.client.force_authenticate(self.other_student)

        response = self.client.get(
            f"/api/practice/sessions/{start_response.data['id']}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_selected_option_must_belong_to_question(self):
        self.create_question("Session question")
        start_response = self.start_practice()
        session = PracticeSession.objects.get(id=start_response.data["id"])
        session_question = session.session_questions.get()
        outside_question = self.create_question("Outside question")
        outside_option = outside_question.options.get(label="A")

        response = self.client.post(
            f"/api/practice/sessions/{session.id}/submit/",
            {
                "answers": [
                    {
                        "session_question": session_question.id,
                        "selected_option": outside_option.id,
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
