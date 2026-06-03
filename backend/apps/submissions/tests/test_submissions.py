from datetime import timedelta
from decimal import Decimal

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
from apps.common.choices import AssignmentStatus, QuestionStatus, SubmissionStatus, UserRole
from apps.question_bank.models import Question, QuestionMedia, QuestionOption
from apps.schools.models import School
from apps.submissions.models import Submission


class SubmissionWorkflowTests(TestCase):
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
        self.session = AcademicSession.objects.create(
            school=self.school,
            name="2026/2027",
            starts_at="2026-09-01",
            ends_at="2027-07-31",
            is_active=True,
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
        self.other_class_arm = ClassArm.objects.create(
            school=self.school,
            class_level=self.class_level,
            name="Science B",
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
            teacher=self.teacher,
            class_arm=self.other_class_arm,
            subject=self.subject,
        )
        TeacherClassSubjectAssignment.objects.create(
            school=self.school,
            teacher=self.other_teacher,
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

    def create_question(self, text, correct_label="A", with_media=False):
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
        for label, option_text in [
            ("A", f"{text} option A"),
            ("B", f"{text} option B"),
            ("C", f"{text} option C"),
            ("D", f"{text} option D"),
        ]:
            QuestionOption.objects.create(
                question=question,
                label=label,
                text=option_text,
                is_correct=label == correct_label,
            )
        if with_media:
            QuestionMedia.objects.create(
                question=question,
                external_url="https://example.com/quadratic-diagram.png",
                description="Quadratic diagram",
                alt_text="A quadratic equation diagram",
                caption="Diagram for the question",
                is_primary=True,
                created_by=self.teacher,
            )
        return question

    def create_published_assignment(
        self,
        *,
        teacher=None,
        class_arm=None,
        count=2,
        first_question_has_media=False,
    ):
        for index in range(count):
            self.create_question(
                f"Question {index + 1}",
                with_media=first_question_has_media and index == 0,
            )

        assignment = create_assignment_from_topic(
            teacher=teacher or self.teacher,
            class_arm=class_arm or self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Quadratic Practice",
            question_count=count,
            due_at=timezone.now() + timedelta(days=1),
        )
        return publish_assignment(assignment, teacher or self.teacher)

    def start_submission(self, assignment):
        self.client.force_authenticate(self.student)
        return self.client.post(
            "/api/submissions/start-assignment/",
            {"assignment": assignment.id},
            format="json",
        )

    def answer_payload(self, submission):
        payload = []
        for assignment_question in submission.assignment.assignment_questions.all():
            selected_option = assignment_question.question.options.order_by("label").first()
            payload.append(
                {
                    "assignment_question": assignment_question.id,
                    "selected_option": selected_option.id,
                }
            )
        return {"answers": payload}

    def test_student_can_start_published_assignment(self):
        assignment = self.create_published_assignment(count=1)

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], SubmissionStatus.IN_PROGRESS)
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertFalse(response.data["questions"][0]["has_diagram"])
        self.assertEqual(response.data["questions"][0]["media"], [])

    def test_student_cannot_start_draft_assignment(self):
        self.create_question("Draft question")
        assignment = create_assignment_from_topic(
            teacher=self.teacher,
            class_arm=self.class_arm,
            subject=self.subject,
            topic=self.topic,
            title="Draft Practice",
            question_count=1,
        )

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 400)

    def test_student_cannot_start_closed_assignment(self):
        assignment = self.create_published_assignment(count=1)
        assignment.status = AssignmentStatus.CLOSED
        assignment.save(update_fields=["status", "updated_at"])

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 400)

    def test_student_cannot_start_before_start_date(self):
        assignment = self.create_published_assignment(count=1)
        assignment.starts_at = timezone.now() + timedelta(days=1)
        assignment.due_at = timezone.now() + timedelta(days=2)
        assignment.save(update_fields=["starts_at", "due_at", "updated_at"])

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 400)
        self.assertIn("has not started", str(response.data))

    def test_student_cannot_start_after_due_when_late_not_allowed(self):
        assignment = self.create_published_assignment(count=1)
        assignment.due_at = timezone.now() - timedelta(hours=1)
        assignment.save(update_fields=["due_at", "updated_at"])

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 400)
        self.assertIn("past its due date", str(response.data))

    def test_student_can_start_and_submit_late_inside_late_window(self):
        assignment = self.create_published_assignment(count=1)
        assignment.due_at = timezone.now() - timedelta(hours=1)
        assignment.allow_late_submissions = True
        assignment.late_submission_deadline = timezone.now() + timedelta(hours=1)
        assignment.save(
            update_fields=[
                "due_at",
                "allow_late_submissions",
                "late_submission_deadline",
                "updated_at",
            ]
        )

        start_response = self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        submit_response = self.client.post(
            f"/api/submissions/{submission.id}/submit/",
            self.answer_payload(submission),
            format="json",
        )
        submission.refresh_from_db()

        self.assertEqual(start_response.status_code, 200)
        self.assertEqual(submit_response.status_code, 200)
        self.assertTrue(submission.is_late)
        self.assertGreater(submission.submitted_after_due_seconds, 0)
        self.assertEqual(submission.deadline_status_at_submit, "late_open")

    def test_student_cannot_submit_after_late_window_closes(self):
        assignment = self.create_published_assignment(count=1)
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        assignment.due_at = timezone.now() - timedelta(hours=2)
        assignment.allow_late_submissions = True
        assignment.late_submission_deadline = timezone.now() - timedelta(hours=1)
        assignment.save(
            update_fields=[
                "due_at",
                "allow_late_submissions",
                "late_submission_deadline",
                "updated_at",
            ]
        )

        response = self.client.post(
            f"/api/submissions/{submission.id}/submit/",
            self.answer_payload(submission),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("past its due date", str(response.data))

    def test_student_cannot_start_another_class_assignment(self):
        assignment = self.create_published_assignment(
            class_arm=self.other_class_arm,
            count=1,
        )

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 400)

    def test_student_assignment_list_returns_deadline_status(self):
        assignment = self.create_published_assignment(count=1)
        assignment.due_at = timezone.now() - timedelta(hours=1)
        assignment.allow_late_submissions = True
        assignment.late_submission_deadline = timezone.now() + timedelta(hours=1)
        assignment.save(
            update_fields=[
                "due_at",
                "allow_late_submissions",
                "late_submission_deadline",
                "updated_at",
            ]
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/submissions/my-assignments/")

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.data if item["id"] == assignment.id)
        self.assertEqual(row["deadline_status"], "late_open")
        self.assertTrue(row["is_overdue"])
        self.assertTrue(row["can_submit_now"])

    def test_question_order_is_stable_after_refresh(self):
        assignment = self.create_published_assignment(count=2)

        first_response = self.start_submission(assignment)
        second_response = self.start_submission(assignment)

        first_order = [item["assignment_question"] for item in first_response.data["questions"]]
        second_order = [item["assignment_question"] for item in second_response.data["questions"]]
        self.assertEqual(first_order, second_order)

    def test_student_cannot_see_correct_answers_before_submission(self):
        assignment = self.create_published_assignment(count=1)

        response = self.start_submission(assignment)

        response_text = str(response.data)
        self.assertNotIn("is_correct", response_text)
        self.assertNotIn("correct_option", response_text)
        self.assertNotIn("Explanation", response_text)

    def test_assignment_attempt_includes_diagram_media_without_answers(self):
        assignment = self.create_published_assignment(
            count=1,
            first_question_has_media=True,
        )

        response = self.start_submission(assignment)

        self.assertEqual(response.status_code, 200)
        question = response.data["questions"][0]
        self.assertTrue(question["has_diagram"])
        self.assertEqual(question["diagram_description"], "Quadratic diagram")
        self.assertEqual(len(question["media"]), 1)
        self.assertEqual(
            question["media"][0]["external_url"],
            "https://example.com/quadratic-diagram.png",
        )
        response_text = str(question)
        self.assertNotIn("is_correct", response_text)
        self.assertNotIn("correct_option", response_text)
        self.assertNotIn("Explanation", response_text)

    def test_assignment_result_includes_diagram_media(self):
        assignment = self.create_published_assignment(
            count=1,
            first_question_has_media=True,
        )
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)

        response = self.client.post(
            f"/api/submissions/{submission.id}/submit/",
            self.answer_payload(submission),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        answer = response.data["answers"][0]
        self.assertTrue(answer["has_diagram"])
        self.assertEqual(answer["diagram_description"], "Quadratic diagram")
        self.assertEqual(len(answer["media"]), 1)
        self.assertEqual(
            answer["media"][0]["external_url"],
            "https://example.com/quadratic-diagram.png",
        )
        self.assertIn("correct_option", answer)
        self.assertIn("explanation", answer)

    def test_student_can_submit_answers_and_grade_is_calculated(self):
        assignment = self.create_published_assignment(count=2)
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)

        response = self.client.post(
            f"/api/submissions/{submission.id}/submit/",
            self.answer_payload(submission),
            format="json",
        )
        submission.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(submission.status, SubmissionStatus.GRADED)
        self.assertEqual(submission.score, 2)
        self.assertEqual(submission.total_marks, 2)
        self.assertEqual(submission.percentage, Decimal("100.00"))

    def test_duplicate_submission_is_blocked(self):
        assignment = self.create_published_assignment(count=1)
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        payload = self.answer_payload(submission)
        self.client.post(f"/api/submissions/{submission.id}/submit/", payload, format="json")

        response = self.client.post(
            f"/api/submissions/{submission.id}/submit/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_teacher_can_view_submissions_for_own_assignment(self):
        assignment = self.create_published_assignment(count=1)
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        self.client.force_authenticate(self.teacher)

        response = self.client.get(f"/api/submissions/{submission.id}/")

        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_view_another_teachers_submission(self):
        assignment = self.create_published_assignment(
            teacher=self.other_teacher,
            count=1,
        )
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        self.client.force_authenticate(self.teacher)

        response = self.client.get(f"/api/submissions/{submission.id}/")

        self.assertEqual(response.status_code, 404)

    def test_school_isolation_prevents_cross_school_access(self):
        assignment = self.create_published_assignment(count=1)
        self.start_submission(assignment)
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        self.client.force_authenticate(self.other_school_admin)

        response = self.client.get(f"/api/submissions/{submission.id}/")

        self.assertEqual(response.status_code, 404)
