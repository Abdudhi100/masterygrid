import io
import zipfile

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.academics.models import ClassLevel, Subject, Topic
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import (
    Question,
    QuestionImportBatch,
    QuestionImportRow,
    QuestionImportRowStatus,
    QuestionMedia,
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

    def zip_upload(self, rows, files=None, filename="questions.zip"):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("questions.csv", self.csv_upload(rows).read())
            for path, content in (files or {}).items():
                archive.writestr(path, content)
        buffer.seek(0)
        return SimpleUploadedFile(
            filename,
            buffer.read(),
            content_type="application/zip",
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
        explanation="",
        has_diagram=False,
        needs_manual_review=False,
        content_hash="",
    ):
        question = Question.objects.create(
            school=self.school,
            subject=self.subject,
            topic=self.topic,
            class_level=self.class_level,
            source=self.source,
            question_text=question_text,
            explanation=explanation,
            content_hash=content_hash,
            difficulty=difficulty,
            status=status,
            is_active=is_active,
            has_diagram=has_diagram,
            needs_manual_review=needs_manual_review,
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

    def create_import_batch_for_question(self, question):
        batch = QuestionImportBatch.objects.create(
            school=self.school,
            uploaded_by=self.school_admin,
            source=self.source,
            title="E2E Quality Import",
            original_filename="questions.csv",
            file_type="csv",
        )
        QuestionImportRow.objects.create(
            batch=batch,
            row_number=2,
            raw_data={"question_text": question.question_text},
            status=QuestionImportRowStatus.IMPORTED,
            question=question,
            content_hash=question.content_hash,
        )
        return batch

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

    def test_valid_csv_preflight_returns_report_without_creating_records(self):
        self.client.force_authenticate(self.school_admin)
        question_count = Question.objects.count()
        batch_count = QuestionImportBatch.objects.count()
        media_count = QuestionMedia.objects.count()

        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([self.import_row()])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["file_type"], "csv")
        self.assertEqual(response.data["total_rows"], 1)
        self.assertEqual(response.data["valid_rows"], 1)
        self.assertEqual(response.data["invalid_rows"], 0)
        self.assertEqual(response.data["warning_rows"], 0)
        self.assertTrue(response.data["can_import"])
        self.assertEqual(Question.objects.count(), question_count)
        self.assertEqual(QuestionImportBatch.objects.count(), batch_count)
        self.assertEqual(QuestionMedia.objects.count(), media_count)

    def test_valid_zip_preflight_returns_report_without_saving_media(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="Preflight ZIP diagram question?",
                            has_diagram="true",
                            diagram_file_name="math_2024_q1.png",
                        )
                    ],
                    {"diagrams/math_2024_q1.png": b"image-bytes"},
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["file_type"], "zip")
        self.assertEqual(response.data["valid_rows"], 1)
        self.assertEqual(response.data["warning_rows"], 0)
        self.assertTrue(response.data["can_import"])
        self.assertFalse(
            Question.objects.filter(
                question_text="Preflight ZIP diagram question?"
            ).exists()
        )
        self.assertEqual(QuestionMedia.objects.count(), 0)

    def test_preflight_missing_correct_option_returns_invalid_row(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([self.import_row(correct_option="")])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["can_import"])
        self.assertEqual(response.data["invalid_rows"], 1)
        self.assertEqual(response.data["summary"]["missing_correct_option"], 1)
        self.assertEqual(response.data["rows"][0]["status"], "invalid")

    def test_preflight_missing_option_returns_invalid_row(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([self.import_row(option_b="")])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["invalid_rows"], 1)
        self.assertEqual(response.data["summary"]["missing_options"], 1)

    def test_preflight_invalid_difficulty_returns_invalid_row(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([self.import_row(difficulty="impossible")])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["invalid_rows"], 1)
        self.assertEqual(response.data["summary"]["invalid_difficulty"], 1)

    def test_preflight_missing_academic_data_appears_in_summary(self):
        self.client.force_authenticate(self.school_admin)
        rows = [
            self.import_row(question_text="Missing subject?", subject="Physics"),
            self.import_row(question_text="Missing class?", class_level="JAMB"),
            self.import_row(question_text="Missing topic?", topic="Measurement"),
        ]

        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload(rows)},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Physics", response.data["summary"]["missing_subjects"])
        self.assertIn("JAMB", response.data["summary"]["missing_class_levels"])
        self.assertIn("Measurement", response.data["summary"]["missing_topics"])
        self.assertEqual(response.data["invalid_rows"], 3)

    def test_preflight_duplicate_inside_file_is_detected(self):
        self.client.force_authenticate(self.school_admin)
        row = self.import_row()
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([row, row])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["duplicate_rows"], 1)
        self.assertEqual(response.data["summary"]["duplicate_questions"], 1)
        self.assertEqual(response.data["rows"][1]["duplicate_type"], "in_file")
        self.assertTrue(response.data["can_import"])

    def test_preflight_existing_database_duplicate_is_detected(self):
        self.client.force_authenticate(self.school_admin)
        import_response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Existing Import",
                "file": self.csv_upload([self.import_row()]),
            },
            format="multipart",
        )
        self.assertEqual(import_response.status_code, 201)

        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([self.import_row()])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["duplicate_rows"], 1)
        self.assertEqual(response.data["summary"]["existing_database_duplicates"], 1)
        self.assertEqual(response.data["rows"][0]["duplicate_type"], "database")

    def test_preflight_zip_missing_image_returns_warning(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="Preflight missing image?",
                            has_diagram="true",
                            diagram_file_name="missing.png",
                        )
                    ],
                    {},
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["can_import"])
        self.assertEqual(response.data["warning_rows"], 1)
        self.assertEqual(response.data["summary"]["missing_diagrams"], 1)
        self.assertIn("Diagram file not found", response.data["rows"][0]["warnings"][0]["message"])

    def test_preflight_diagram_url_wins_over_zip_image_warning(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="Preflight URL wins?",
                            has_diagram="true",
                            diagram_file_name="math_2024_q1.png",
                            diagram_url="https://example.com/diagram.png",
                        )
                    ],
                    {"diagrams/math_2024_q1.png": b"image-bytes"},
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["warning_rows"], 1)
        self.assertIn("diagram_url was used", response.data["rows"][0]["warnings"][0]["message"])

    def test_preflight_unsafe_zip_path_is_rejected(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {
                "file": self.zip_upload(
                    [self.import_row()],
                    {"../evil.py": b"print('bad')"},
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsafe ZIP path", str(response.data))

    def test_student_cannot_preflight_import(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/question-bank/imports/preflight/",
            {"file": self.csv_upload([self.import_row()])},
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)

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
        self.assertEqual(response.data["warning_rows"], 1)
        self.assertIn("Warning", row.warning_message)

    def test_import_zip_attaches_matching_diagram_image(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "ZIP Diagram Import",
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="ZIP diagram question?",
                            has_diagram="true",
                            diagram_file_name="physics_2025_q1.png",
                            diagram_description="A physics diagram",
                        )
                    ],
                    {
                        "diagrams/physics_2025_q1.png": b"fake image bytes",
                    },
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(response.data["successful_rows"], 1)
        self.assertEqual(response.data["warning_rows"], 0)
        question = Question.objects.get(question_text="ZIP diagram question?")
        self.assertEqual(question.status, QuestionStatus.DRAFT)
        self.assertTrue(question.has_diagram)
        self.assertFalse(question.needs_manual_review)
        media = question.media.get()
        self.assertTrue(media.image.name.endswith(".png"))
        self.assertEqual(media.original_filename, "physics_2025_q1.png")
        self.assertEqual(media.description, "A physics diagram")

    def test_import_zip_matches_diagram_full_path(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "ZIP Path Diagram Import",
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="ZIP full path diagram question?",
                            has_diagram="true",
                            diagram_file_name="diagrams/nested/physics_2025_q2.jpg",
                        )
                    ],
                    {
                        "diagrams/nested/physics_2025_q2.jpg": b"fake jpg bytes",
                    },
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        question = Question.objects.get(
            question_text="ZIP full path diagram question?"
        )
        self.assertEqual(question.media.get().original_filename, "physics_2025_q2.jpg")

    def test_import_zip_missing_image_adds_warning_and_manual_review(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "ZIP Missing Diagram Import",
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="ZIP missing diagram question?",
                            has_diagram="true",
                            diagram_file_name="missing.png",
                        )
                    ],
                    {},
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        self.assertEqual(response.data["warning_rows"], 1)
        question = Question.objects.get(question_text="ZIP missing diagram question?")
        self.assertTrue(question.has_diagram)
        self.assertTrue(question.needs_manual_review)
        self.assertEqual(question.media.count(), 0)
        row = QuestionImportBatch.objects.get(id=response.data["id"]).rows.get()
        self.assertIn("Diagram file not found in ZIP", row.warning_message)

    def test_import_zip_rejects_unsafe_path(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Unsafe ZIP Import",
                "file": self.zip_upload(
                    [self.import_row()],
                    {"../evil.py": b"print('bad')"},
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsafe ZIP path", str(response.data))

    def test_import_zip_rejects_unsupported_diagram_type(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Unsupported ZIP Import",
                "file": self.zip_upload(
                    [self.import_row()],
                    {"diagrams/vector.svg": b"<svg></svg>"},
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported diagram image type", str(response.data))

    def test_import_zip_ambiguous_basename_fails_row(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "Ambiguous ZIP Import",
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="Ambiguous diagram question?",
                            has_diagram="true",
                            diagram_file_name="figure.png",
                        )
                    ],
                    {
                        "diagrams/a/figure.png": b"first",
                        "diagrams/b/figure.png": b"second",
                    },
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["failed_rows"], 1)
        row = QuestionImportBatch.objects.get(id=response.data["id"]).rows.get()
        self.assertEqual(row.status, QuestionImportRowStatus.FAILED)
        self.assertIn("ambiguous", row.error_message)

    def test_import_zip_diagram_url_takes_precedence_over_zip_image(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.post(
            "/api/question-bank/imports/",
            {
                "title": "ZIP URL Precedence Import",
                "file": self.zip_upload(
                    [
                        self.import_row(
                            question_text="URL precedence diagram question?",
                            has_diagram="true",
                            diagram_file_name="physics_2025_q1.png",
                            diagram_url="https://example.com/preferred.png",
                        )
                    ],
                    {
                        "diagrams/physics_2025_q1.png": b"ignored",
                    },
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["successful_rows"], 1)
        self.assertEqual(response.data["warning_rows"], 1)
        question = Question.objects.get(question_text="URL precedence diagram question?")
        media = question.media.get()
        self.assertEqual(media.external_url, "https://example.com/preferred.png")
        self.assertFalse(bool(media.image))
        row = QuestionImportBatch.objects.get(id=response.data["id"]).rows.get()
        self.assertIn("diagram_url was used", row.warning_message)

    def test_student_cannot_search_approved_question_bank_directly(self):
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/question-bank/questions/search-approved/")

        self.assertEqual(response.status_code, 403)

    def test_quality_dashboard_reports_core_sections(self):
        missing_explanation = self.create_stored_question(
            question_text="E2E quality missing explanation?",
            explanation="",
        )
        self.create_import_batch_for_question(missing_explanation)
        diagram_issue = self.create_stored_question(
            question_text="E2E quality diagram issue?",
            explanation="Diagram question explanation.",
            has_diagram=True,
            needs_manual_review=True,
        )
        ready_question = self.create_stored_question(
            question_text="E2E quality ready for approval?",
            explanation="Ready question explanation.",
        )
        duplicate_one = self.create_stored_question(
            question_text="E2E duplicate question one?",
            explanation="Duplicate explanation.",
            content_hash="duplicate-hash",
        )
        duplicate_two = self.create_stored_question(
            question_text="E2E duplicate question two?",
            explanation="Duplicate explanation.",
            content_hash="duplicate-hash",
        )

        self.client.force_authenticate(self.school_admin)
        response = self.client.get("/api/question-bank/quality-dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["summary"]["draft_count"], 5)
        self.assertGreaterEqual(response.data["summary"]["missing_explanation_count"], 1)
        self.assertGreaterEqual(response.data["summary"]["diagram_issue_count"], 1)
        self.assertGreaterEqual(response.data["summary"]["duplicate_suspect_count"], 2)
        ready_ids = [
            row["id"] for row in response.data["sections"]["ready_for_approval"]
        ]
        self.assertIn(ready_question.id, ready_ids)
        imported_ids = [row["id"] for row in response.data["sections"]["imported_drafts"]]
        self.assertIn(missing_explanation.id, imported_ids)
        diagram_ids = [row["id"] for row in response.data["sections"]["diagram_issues"]]
        self.assertIn(diagram_issue.id, diagram_ids)
        duplicate_ids = [row["id"] for row in response.data["sections"]["duplicate_suspects"]]
        self.assertIn(duplicate_one.id, duplicate_ids)
        self.assertIn(duplicate_two.id, duplicate_ids)

    def test_quality_dashboard_blocks_students_and_teachers(self):
        for user in [self.student, self.teacher]:
            self.client.force_authenticate(user)
            response = self.client.get("/api/question-bank/quality-dashboard/")
            self.assertEqual(response.status_code, 403)

    def test_bulk_approve_ready_question(self):
        ready_question = self.create_stored_question(
            question_text="E2E bulk approve ready?",
            explanation="Ready question explanation.",
        )
        self.client.force_authenticate(self.school_admin)

        response = self.client.post(
            "/api/question-bank/questions/bulk-action/",
            {"question_ids": [ready_question.id], "action": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["status"], "success")
        ready_question.refresh_from_db()
        self.assertEqual(ready_question.status, QuestionStatus.APPROVED)

    def test_bulk_approve_rejects_question_with_quality_issue(self):
        missing_explanation = self.create_stored_question(
            question_text="E2E bulk approve not ready?",
            explanation="",
        )
        self.client.force_authenticate(self.school_admin)

        response = self.client.post(
            "/api/question-bank/questions/bulk-action/",
            {"question_ids": [missing_explanation.id], "action": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["status"], "failed")
        missing_explanation.refresh_from_db()
        self.assertEqual(missing_explanation.status, QuestionStatus.DRAFT)
