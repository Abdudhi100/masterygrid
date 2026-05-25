import os
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
from apps.accounts.models import StudentProfile, TeacherProfile
from apps.ai_generation.models import AIQuestionSuggestionRun
from apps.assignments.models import Assignment, AssignmentQuestion
from apps.practice.models import PracticeAnswer, PracticeSession, PracticeSessionQuestion
from apps.question_bank.models import (
    Question,
    QuestionImportBatch,
    QuestionImportRow,
    QuestionMedia,
    QuestionOption,
    QuestionSource,
)
from apps.submissions.models import StudentAnswer, Submission

User = get_user_model()

E2E_EMAIL_DOMAIN = "@masterygrid.test"
E2E_MARKER = "E2E"
DEMO_EMAIL_DOMAIN = "@masterygrid.demo"


@dataclass
class CleanupItem:
    label: str
    queryset: QuerySet


class Command(BaseCommand):
    help = "Safely dry-run or delete clearly identifiable Playwright E2E test data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually delete matched E2E data. Without this, the command is dry-run only.",
        )
        parser.add_argument(
            "--run-id",
            help="Restrict cleanup to records containing a specific E2E run id.",
        )
        parser.add_argument(
            "--older-than-days",
            type=int,
            help="Restrict cleanup to E2E data created more than this many days ago.",
        )
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Required before deleting when DJANGO_ENV=prod or DEBUG=False.",
        )
        parser.add_argument(
            "--school-id",
            type=int,
            help="Restrict school-scoped cleanup to one school id.",
        )

    def handle(self, *args, **options):
        self.confirm = options["confirm"]
        self.run_id = (options.get("run_id") or "").strip()
        self.school_id = options.get("school_id")
        self.cutoff = self.get_cutoff(options.get("older_than_days"))

        self.enforce_safety(options)

        plan = self.build_plan()
        counts = [(item.label, item.queryset.count()) for item in plan]
        total = sum(count for _label, count in counts)

        self.print_plan(counts, total)

        if not self.confirm:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run only. Re-run with --confirm to delete matched E2E data."
                )
            )
            return

        with transaction.atomic():
            deleted_total = 0
            for item in plan:
                count = item.queryset.count()
                if count:
                    item.queryset.delete()
                deleted_total += count

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_total} matched E2E records.")
        )

    def get_cutoff(self, older_than_days):
        if older_than_days is None:
            return None
        if older_than_days < 0:
            raise CommandError("--older-than-days must be zero or greater.")
        return timezone.now() - timedelta(days=older_than_days)

    def enforce_safety(self, options):
        is_production_like = os.environ.get("DJANGO_ENV") == "prod" or not settings.DEBUG

        if self.confirm and is_production_like and not options["allow_production"]:
            raise CommandError(
                "Refusing to delete E2E data in production-like settings. "
                "Pass --allow-production only for an intentional staging/demo cleanup."
            )

    def e2e_text_q(self, *fields):
        query = Q()
        for field in fields:
            query |= Q(**{f"{field}__icontains": E2E_MARKER})
        if self.run_id:
            run_query = Q()
            for field in fields:
                run_query |= Q(**{f"{field}__icontains": self.run_id})
            query &= run_query
        return query

    def e2e_user_q(self):
        query = Q(email__iendswith=E2E_EMAIL_DOMAIN)
        if self.run_id:
            query &= (
                Q(email__icontains=self.run_id)
                | Q(full_name__icontains=self.run_id)
            )
        return query

    def apply_common_filters(self, queryset):
        model = queryset.model
        fields = {field.name for field in model._meta.get_fields()}

        if self.school_id and "school" in fields:
            queryset = queryset.filter(school_id=self.school_id)

        if self.cutoff and "created_at" in fields:
            queryset = queryset.filter(created_at__lt=self.cutoff)

        return queryset.distinct()

    def ids(self, queryset):
        return list(queryset.values_list("id", flat=True))

    def build_plan(self):
        e2e_users = self.apply_common_filters(
            User.objects.filter(self.e2e_user_q()).exclude(
                email__iendswith=DEMO_EMAIL_DOMAIN
            )
        )
        user_ids = self.ids(e2e_users)

        sessions = self.apply_common_filters(
            AcademicSession.objects.filter(self.e2e_text_q("name"))
        )
        session_ids = self.ids(sessions)

        terms = self.apply_common_filters(
            Term.objects.filter(academic_session_id__in=session_ids)
        )
        term_ids = self.ids(terms)

        class_levels = self.apply_common_filters(
            ClassLevel.objects.filter(self.e2e_text_q("name", "description"))
        )
        class_level_ids = self.ids(class_levels)

        class_arms = self.apply_common_filters(
            ClassArm.objects.filter(
                self.e2e_text_q("name", "description")
                | Q(class_level_id__in=class_level_ids)
            )
        )
        class_arm_ids = self.ids(class_arms)

        subjects = self.apply_common_filters(
            Subject.objects.filter(self.e2e_text_q("name", "code", "description"))
        )
        subject_ids = self.ids(subjects)

        topics = self.apply_common_filters(
            Topic.objects.filter(
                self.e2e_text_q("title", "description")
                | Q(subject_id__in=subject_ids)
                | Q(class_level_id__in=class_level_ids)
            )
        )
        topic_ids = self.ids(topics)

        sources_by_name = QuestionSource.objects.filter(
            self.e2e_text_q("name", "description")
        )
        if self.cutoff:
            sources_by_name = sources_by_name.filter(created_at__lt=self.cutoff)
        source_name_ids = self.ids(sources_by_name)

        questions = self.apply_common_filters(
            Question.objects.filter(
                self.e2e_text_q("question_text", "explanation", "diagram_description")
                | Q(created_by_id__in=user_ids)
                | Q(reviewed_by_id__in=user_ids)
                | Q(subject_id__in=subject_ids)
                | Q(topic_id__in=topic_ids)
                | Q(class_level_id__in=class_level_ids)
                | Q(source_id__in=source_name_ids)
            )
        )
        question_ids = self.ids(questions)

        imports = self.apply_common_filters(
            QuestionImportBatch.objects.filter(
                self.e2e_text_q("title", "original_filename", "error_summary")
                | Q(uploaded_by_id__in=user_ids)
                | Q(source_id__in=source_name_ids)
            )
        )
        import_ids = self.ids(imports)

        source_ids = set(source_name_ids)
        source_ids.update(
            questions.exclude(source_id__isnull=True).values_list("source_id", flat=True)
        )
        source_ids.update(
            imports.exclude(source_id__isnull=True).values_list("source_id", flat=True)
        )
        sources = QuestionSource.objects.filter(id__in=source_ids)
        non_e2e_source_refs = set(
            Question.objects.filter(source_id__in=source_ids)
            .exclude(id__in=question_ids)
            .values_list("source_id", flat=True)
        )
        non_e2e_source_refs.update(
            QuestionImportBatch.objects.filter(source_id__in=source_ids)
            .exclude(id__in=import_ids)
            .values_list("source_id", flat=True)
        )
        sources = sources.exclude(id__in=non_e2e_source_refs)
        if self.run_id:
            sources = sources.filter(self.e2e_text_q("name", "description"))
        if self.cutoff:
            sources = sources.filter(created_at__lt=self.cutoff)

        assignments = self.apply_common_filters(
            Assignment.objects.filter(
                self.e2e_text_q("title", "instructions")
                | Q(teacher_id__in=user_ids)
                | Q(class_arm_id__in=class_arm_ids)
                | Q(subject_id__in=subject_ids)
                | Q(topic_id__in=topic_ids)
            )
        )
        assignment_ids = self.ids(assignments)

        submissions = self.apply_common_filters(
            Submission.objects.filter(
                Q(student_id__in=user_ids) | Q(assignment_id__in=assignment_ids)
            )
        )
        submission_ids = self.ids(submissions)

        practice_sessions = self.apply_common_filters(
            PracticeSession.objects.filter(
                Q(student_id__in=user_ids)
                | Q(subject_id__in=subject_ids)
                | Q(topic_id__in=topic_ids)
                | Q(class_level_id__in=class_level_ids)
                | Q(class_arm_id__in=class_arm_ids)
            )
        )
        practice_session_ids = self.ids(practice_sessions)

        lesson_logs = self.apply_common_filters(
            LessonLog.objects.filter(
                self.e2e_text_q("notes")
                | Q(teacher_id__in=user_ids)
                | Q(class_arm_id__in=class_arm_ids)
                | Q(subject_id__in=subject_ids)
                | Q(topic_id__in=topic_ids)
                | Q(academic_session_id__in=session_ids)
                | Q(term_id__in=term_ids)
            )
        )

        teacher_assignments = self.apply_common_filters(
            TeacherClassSubjectAssignment.objects.filter(
                Q(teacher_id__in=user_ids)
                | Q(class_arm_id__in=class_arm_ids)
                | Q(subject_id__in=subject_ids)
                | Q(academic_session_id__in=session_ids)
                | Q(term_id__in=term_ids)
            )
        )

        enrollments = self.apply_common_filters(
            StudentEnrollment.objects.filter(
                Q(student_id__in=user_ids)
                | Q(class_arm_id__in=class_arm_ids)
                | Q(academic_session_id__in=session_ids)
                | Q(term_id__in=term_ids)
            )
        )

        ai_runs = self.apply_common_filters(
            AIQuestionSuggestionRun.objects.filter(
                Q(requested_by_id__in=user_ids)
                | Q(applied_by_id__in=user_ids)
                | Q(question_id__in=question_ids)
                | Q(suggested_topic_id__in=topic_ids)
            )
        )

        assignment_questions = self.apply_common_filters(
            AssignmentQuestion.objects.filter(
                Q(assignment_id__in=assignment_ids) | Q(question_id__in=question_ids)
            )
        )
        assignment_question_ids = self.ids(assignment_questions)

        student_answers = self.apply_common_filters(
            StudentAnswer.objects.filter(
                Q(submission_id__in=submission_ids)
                | Q(assignment_question_id__in=assignment_question_ids)
                | Q(selected_option__question_id__in=question_ids)
            )
        )

        practice_session_questions = self.apply_common_filters(
            PracticeSessionQuestion.objects.filter(
                Q(session_id__in=practice_session_ids) | Q(question_id__in=question_ids)
            )
        )
        practice_session_question_ids = self.ids(practice_session_questions)

        practice_answers = self.apply_common_filters(
            PracticeAnswer.objects.filter(
                Q(session_id__in=practice_session_ids)
                | Q(session_question_id__in=practice_session_question_ids)
                | Q(selected_option__question_id__in=question_ids)
            )
        )

        import_rows = self.apply_common_filters(
            QuestionImportRow.objects.filter(
                Q(batch_id__in=import_ids) | Q(question_id__in=question_ids)
            )
        )

        media = self.apply_common_filters(
            QuestionMedia.objects.filter(question_id__in=question_ids)
        )

        options = self.apply_common_filters(
            QuestionOption.objects.filter(question_id__in=question_ids)
        )

        teacher_profiles = self.apply_common_filters(
            TeacherProfile.objects.filter(Q(user_id__in=user_ids) | self.e2e_text_q("staff_id"))
        )
        student_profiles = self.apply_common_filters(
            StudentProfile.objects.filter(
                Q(user_id__in=user_ids)
                | self.e2e_text_q("admission_number", "guardian_name")
            )
        )

        return [
            CleanupItem("AI suggestion runs", ai_runs),
            CleanupItem("Practice answers", practice_answers),
            CleanupItem("Practice session questions", practice_session_questions),
            CleanupItem("Practice sessions", practice_sessions),
            CleanupItem("Student answers", student_answers),
            CleanupItem("Submissions", submissions),
            CleanupItem("Assignment questions", assignment_questions),
            CleanupItem("Assignments", assignments),
            CleanupItem("Question import rows", import_rows),
            CleanupItem("Question import batches", imports),
            CleanupItem("Lesson logs", lesson_logs),
            CleanupItem("Teacher assignments", teacher_assignments),
            CleanupItem("Student enrollments", enrollments),
            CleanupItem("Question media", media),
            CleanupItem("Question options", options),
            CleanupItem("Questions", questions),
            CleanupItem("Question sources", sources),
            CleanupItem("Topics", topics),
            CleanupItem("Subjects", subjects),
            CleanupItem("Class arms", class_arms),
            CleanupItem("Class levels", class_levels),
            CleanupItem("Terms", terms),
            CleanupItem("Academic sessions", sessions),
            CleanupItem("Teacher profiles", teacher_profiles),
            CleanupItem("Student profiles", student_profiles),
            CleanupItem("Users", e2e_users),
        ]

    def print_plan(self, counts, total):
        self.stdout.write("E2E cleanup deletion plan:")
        self.stdout.write(f"- mode: {'DELETE' if self.confirm else 'dry-run'}")
        if self.run_id:
            self.stdout.write(f"- run id: {self.run_id}")
        if self.school_id:
            self.stdout.write(f"- school id: {self.school_id}")
        if self.cutoff:
            self.stdout.write(f"- older than: {self.cutoff.isoformat()}")
        self.stdout.write("")

        for label, count in counts:
            self.stdout.write(f"- {label}: {count}")

        self.stdout.write("")
        self.stdout.write(f"Total matched records: {total}")
