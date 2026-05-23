from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.academics.models import ClassLevel, Subject, Topic
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import (
    Question,
    QuestionImportBatch,
    QuestionImportRowStatus,
    QuestionOption,
    QuestionSource,
)
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

    def csv_upload(self, rows):
        header = [
            "subject",
            "class_level",
            "topic",
            "source_name",
            "source_type",
            "exam_body",
            "year",
            "difficulty",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "explanation",
            "has_diagram",
            "diagram_file_name",
            "diagram_url",
            "diagram_description",
            "needs_manual_review",
        ]
        lines = [",".join(header)]
        for row in rows:
            values = [str(row.get(column, "")).replace(",", ";") for column in header]
            lines.append(",".join(values))
        return SimpleUploadedFile(
            "questions.csv",
            "\n".join(lines).encode("utf-8"),
            content_type="text/csv",
        )

    def import_row(self, **overrides):
        data = {
            "subject": "Mathematics",
            "class_level": "SS2",
            "topic": "Quadratic Equations",
            "source_name": "JAMB Mathematics",
            "source_type": "jamb_past_question",
            "exam_body": "JAMB",
            "year": "2024",
            "difficulty": "medium",
            "question_text": "What is the sum of roots of x^2 - 5x + 6 = 0?",
            "option_a": "2",
            "option_b": "3",
            "option_c": "5",
            "option_d": "6",
            "correct_option": "C",
            "explanation": "The sum of roots is -b/a = 5.",
        }
        data.update(overrides)
        return data

    def create_stored_question(
        self,
        *,
        status=QuestionStatus.DRAFT,
        difficulty="medium",
        is_active=True,
        question_text="Stored question?",
        created_by=None,
    ):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            source=self.source,
            question_text=question_text,
            difficulty=difficulty,
            status=status,
            is_active=is_active,
            created_by=created_by or self.teacher,
        )
        for label, text, is_correct in [
            ("A", "Option A", False),
            ("B", "Option B", True),
            ("C", "Option C", False),
            ("D", "Option D", False),
        ]:
            QuestionOption.objects.create(
                question=question,
                label=label,
                text=text,
                is_correct=is_correct,
            )
        return question

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

    def test_school_admin_can_import_csv_for_own_school(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "JAMB Mathematics Import",
                "file": self.csv_upload([self.import_row()]),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(response.data["successful_rows"], 1)
        question = Question.objects.get(
            question_text="What is the sum of roots of x^2 - 5x + 6 = 0?"
        )
        self.assertEqual(question.status, QuestionStatus.DRAFT)
        self.assertEqual(question.school, self.school)
        self.assertEqual(question.options.count(), 4)
        self.assertEqual(question.options.get(is_correct=True).label, "C")
        self.assertFalse(question.is_usable_for_assignment)

    def test_student_cannot_import_questions(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Blocked Import",
                "file": self.csv_upload([self.import_row()]),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_import_row_is_marked_failed(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Invalid Import",
                "file": self.csv_upload([self.import_row(difficulty="impossible")]),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "completed_with_errors")
        self.assertEqual(response.data["failed_rows"], 1)
        batch = QuestionImportBatch.objects.get(id=response.data["id"])
        row = batch.rows.get()
        self.assertEqual(row.status, QuestionImportRowStatus.FAILED)
        self.assertIn("Difficulty", row.error_message)

    def test_duplicate_import_row_is_marked_duplicate(self):
        self.client.force_authenticate(self.school_admin)
        duplicate = self.import_row()
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Duplicate Import",
                "file": self.csv_upload([duplicate, duplicate]),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        self.assertEqual(response.data["duplicate_rows"], 1)
        batch = QuestionImportBatch.objects.get(id=response.data["id"])
        self.assertEqual(
            batch.rows.filter(status=QuestionImportRowStatus.DUPLICATE).count(),
            1,
        )

    def test_approved_search_returns_only_approved_active_questions(self):
        approved = self.create_stored_question(
            status=QuestionStatus.APPROVED,
            difficulty="hard",
            question_text="Approved hard question?",
        )
        self.create_stored_question(
            status=QuestionStatus.DRAFT,
            difficulty="hard",
            question_text="Draft hard question?",
        )
        self.create_stored_question(
            status=QuestionStatus.APPROVED,
            difficulty="hard",
            is_active=False,
            question_text="Inactive approved question?",
        )
        self.client.force_authenticate(self.teacher)

        response = self.client.get(
            "/api/question-bank/questions/search-approved/",
            {
                "subject": self.subject.id,
                "topic": self.topic.id,
                "class_level": self.class_level.id,
                "difficulty": "hard",
                "count": 5,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["available_count"], 1)
        self.assertIn("Only 1 approved active question", response.data["message"])
        self.assertEqual(response.data["results"][0]["id"], approved.id)
        self.assertEqual(len(response.data["results"][0]["options"]), 4)

    def test_question_without_media_still_serializes(self):
        question = self.create_stored_question()
        self.client.force_authenticate(self.teacher)

        response = self.client.get(f"/api/question-bank/questions/{question.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["has_diagram"])
        self.assertFalse(response.data["needs_manual_review"])
        self.assertEqual(response.data["media"], [])

    def test_question_with_external_url_media_is_exposed(self):
        question = self.create_stored_question(created_by=self.teacher)
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            f"/api/question-bank/questions/{question.id}/media/",
            {
                "external_url": "https://example.com/diagram.png",
                "description": "Triangle diagram",
                "alt_text": "A triangle diagram",
                "caption": "Triangle",
                "is_primary": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        question.refresh_from_db()
        self.assertTrue(question.has_diagram)
        self.assertEqual(question.diagram_description, "Triangle diagram")

        detail_response = self.client.get(f"/api/question-bank/questions/{question.id}/")
        self.assertEqual(len(detail_response.data["media"]), 1)
        self.assertEqual(
            detail_response.data["media"][0]["external_url"],
            "https://example.com/diagram.png",
        )

    def test_media_requires_image_or_external_url(self):
        question = self.create_stored_question(created_by=self.teacher)
        self.client.force_authenticate(self.teacher)

        response = self.client.post(
            f"/api/question-bank/questions/{question.id}/media/",
            {"description": "Missing image and URL"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_import_csv_with_diagram_url_creates_media(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Diagram Import",
                "file": self.csv_upload(
                    [
                        self.import_row(
                            question_text="Diagram question?",
                            has_diagram="yes",
                            diagram_url="https://example.com/math-diagram.png",
                            diagram_description="A quadratic graph",
                        )
                    ]
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        question = Question.objects.get(question_text="Diagram question?")
        self.assertEqual(question.status, QuestionStatus.DRAFT)
        self.assertTrue(question.has_diagram)
        self.assertEqual(question.diagram_description, "A quadratic graph")
        media = question.media.get()
        self.assertEqual(media.external_url, "https://example.com/math-diagram.png")
        self.assertTrue(media.is_primary)

    def test_import_csv_with_diagram_file_name_marks_manual_review(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Diagram Filename Import",
                "file": self.csv_upload(
                    [
                        self.import_row(
                            question_text="Manual diagram question?",
                            has_diagram="true",
                            diagram_file_name="diagram-001.png",
                            diagram_description="A missing diagram",
                        )
                    ]
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        question = Question.objects.get(question_text="Manual diagram question?")
        self.assertEqual(question.status, QuestionStatus.DRAFT)
        self.assertTrue(question.has_diagram)
        self.assertTrue(question.needs_manual_review)
        self.assertEqual(question.media.count(), 0)
        row = QuestionImportBatch.objects.get(id=response.data["id"]).rows.get()
        self.assertEqual(row.status, QuestionImportRowStatus.IMPORTED)
        self.assertIn("Warning", row.error_message)

    def test_student_cannot_search_approved_question_bank_directly(self):
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/question-bank/questions/search-approved/")

        self.assertEqual(response.status_code, 403)
