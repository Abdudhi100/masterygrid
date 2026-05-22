from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    TermName,
    Topic,
)
from apps.accounts.models import StudentProfile, TeacherProfile
from apps.assignments.models import Assignment, AssignmentQuestion
from apps.common.choices import AssignmentStatus, QuestionStatus, SubmissionStatus, UserRole
from apps.question_bank.models import (
    Question,
    QuestionDifficulty,
    QuestionOption,
    QuestionSource,
    QuestionSourceType,
)
from apps.question_bank.services import validate_persisted_question_options
from apps.schools.models import School
from apps.submissions.models import StudentAnswer, Submission

User = get_user_model()

DEMO_PASSWORD = "Password123!"
DEMO_SCHOOL_NAME = "MasteryGrid Demo School"
DEMO_SCHOOL_SLUG = slugify(DEMO_SCHOOL_NAME)


def aware_datetime(year, month, day, hour=0, minute=0):
    return timezone.make_aware(
        datetime(year, month, day, hour, minute),
        timezone.get_current_timezone(),
    )


QUESTION_SPECS = [
    {
        "topic": "Quadratic Equations",
        "text": "If x^2 - 5x + 6 = 0, what are the values of x?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "Factor x^2 - 5x + 6 as (x - 2)(x - 3), so x = 2 or x = 3.",
        "options": [
            ("A", "1 and 6", False),
            ("B", "2 and 3", True),
            ("C", "-2 and -3", False),
            ("D", "3 and 5", False),
        ],
    },
    {
        "topic": "Quadratic Equations",
        "text": "What is the sum of the roots of 2x^2 - 7x + 3 = 0?",
        "difficulty": QuestionDifficulty.MEDIUM,
        "explanation": "For ax^2 + bx + c = 0, the sum of roots is -b/a. Here it is 7/2.",
        "options": [
            ("A", "7/2", True),
            ("B", "-7/2", False),
            ("C", "3/2", False),
            ("D", "2/7", False),
        ],
    },
    {
        "topic": "Quadratic Equations",
        "text": "What is the product of the roots of 3x^2 + 2x - 8 = 0?",
        "difficulty": QuestionDifficulty.MEDIUM,
        "explanation": "For ax^2 + bx + c = 0, the product of roots is c/a, which is -8/3.",
        "options": [
            ("A", "8/3", False),
            ("B", "-2/3", False),
            ("C", "-8/3", True),
            ("D", "3/8", False),
        ],
    },
    {
        "topic": "Quadratic Equations",
        "text": "What is the discriminant of x^2 + 4x + 4 = 0?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "The discriminant is b^2 - 4ac = 16 - 16 = 0.",
        "options": [
            ("A", "0", True),
            ("B", "4", False),
            ("C", "8", False),
            ("D", "16", False),
        ],
    },
    {
        "topic": "Quadratic Equations",
        "text": "Which expression is the factorised form of x^2 - 9?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "x^2 - 9 is a difference of two squares: (x - 3)(x + 3).",
        "options": [
            ("A", "(x - 9)(x + 1)", False),
            ("B", "(x - 3)(x + 3)", True),
            ("C", "(x - 3)(x - 3)", False),
            ("D", "(x + 9)(x - 1)", False),
        ],
    },
    {
        "topic": "Simultaneous Equations",
        "text": "Solve x + y = 7 and x - y = 1.",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "Adding the equations gives 2x = 8, so x = 4 and y = 3.",
        "options": [
            ("A", "x = 3, y = 4", False),
            ("B", "x = 4, y = 3", True),
            ("C", "x = 5, y = 2", False),
            ("D", "x = 2, y = 5", False),
        ],
    },
    {
        "topic": "Simultaneous Equations",
        "text": "Solve 2x + y = 10 and x + y = 6.",
        "difficulty": QuestionDifficulty.MEDIUM,
        "explanation": "Subtracting x + y = 6 from 2x + y = 10 gives x = 4, then y = 2.",
        "options": [
            ("A", "x = 4, y = 2", True),
            ("B", "x = 2, y = 4", False),
            ("C", "x = 5, y = 1", False),
            ("D", "x = 3, y = 3", False),
        ],
    },
    {
        "topic": "Simultaneous Equations",
        "text": "If 3x - 2y = 4 and x + y = 5, what is x?",
        "difficulty": QuestionDifficulty.HARD,
        "explanation": "From x + y = 5, y = 5 - x. Substitute to get 5x = 14, so x = 14/5.",
        "options": [
            ("A", "2", False),
            ("B", "5/14", False),
            ("C", "14/5", True),
            ("D", "5", False),
        ],
    },
    {
        "topic": "Simultaneous Equations",
        "text": "If x + 2y = 9 and x - y = 3, what is y?",
        "difficulty": QuestionDifficulty.MEDIUM,
        "explanation": "From x - y = 3, x = y + 3. Substitute to get 3y + 3 = 9, so y = 2.",
        "options": [
            ("A", "1", False),
            ("B", "2", True),
            ("C", "3", False),
            ("D", "4", False),
        ],
    },
    {
        "topic": "Simultaneous Equations",
        "text": "What is obtained by adding 2x + 3y = 12 and x - 3y = 6?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "Adding eliminates y and gives 3x = 18.",
        "options": [
            ("A", "x = 18", False),
            ("B", "3x = 18", True),
            ("C", "3y = 18", False),
            ("D", "x + y = 18", False),
        ],
    },
    {
        "topic": "Logarithms",
        "text": "What is log10 1000?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "10 raised to the power 3 equals 1000, so log10 1000 = 3.",
        "options": [
            ("A", "2", False),
            ("B", "3", True),
            ("C", "10", False),
            ("D", "100", False),
        ],
    },
    {
        "topic": "Logarithms",
        "text": "What is log2 8?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "2 raised to the power 3 equals 8, so log2 8 = 3.",
        "options": [
            ("A", "2", False),
            ("B", "3", True),
            ("C", "4", False),
            ("D", "8", False),
        ],
    },
    {
        "topic": "Logarithms",
        "text": "For a positive a not equal to 1, what is log_a a?",
        "difficulty": QuestionDifficulty.MEDIUM,
        "explanation": "Any valid base raised to the power 1 equals itself, so log_a a = 1.",
        "options": [
            ("A", "0", False),
            ("B", "1", True),
            ("C", "a", False),
            ("D", "10", False),
        ],
    },
    {
        "topic": "Logarithms",
        "text": "What is log10 1?",
        "difficulty": QuestionDifficulty.EASY,
        "explanation": "10 raised to the power 0 equals 1, so log10 1 = 0.",
        "options": [
            ("A", "0", True),
            ("B", "1", False),
            ("C", "10", False),
            ("D", "-1", False),
        ],
    },
    {
        "topic": "Logarithms",
        "text": "What is log3 81?",
        "difficulty": QuestionDifficulty.MEDIUM,
        "explanation": "3 raised to the power 4 equals 81, so log3 81 = 4.",
        "options": [
            ("A", "3", False),
            ("B", "4", True),
            ("C", "9", False),
            ("D", "27", False),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed realistic MasteryGrid demo data for local pilot testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-submissions",
            action="store_true",
            help="Create graded demo submissions for the three seeded students.",
        )

    def handle(self, *args, **options):
        self.summary = defaultdict(lambda: {"created": 0, "found": 0})

        with transaction.atomic():
            context = self.seed_core_data()
            if options["with_submissions"]:
                self.seed_submissions(context)

        self.print_summary(with_submissions=options["with_submissions"])

    def note(self, section, created):
        key = "created" if created else "found"
        self.summary[section][key] += 1

    def save_clean(self, instance, update_fields=None):
        instance.full_clean()
        instance.save(update_fields=update_fields)
        return instance

    def seed_core_data(self):
        school, created = School.objects.update_or_create(
            slug=DEMO_SCHOOL_SLUG,
            defaults={
                "name": DEMO_SCHOOL_NAME,
                "email": "hello@masterygrid.demo",
                "phone": "+2348012345678",
                "address": "12 Demo Avenue, Ikeja, Lagos, Nigeria",
                "is_active": True,
            },
        )
        self.note("school", created)
        self.save_clean(school)

        admin = self.ensure_user(
            email="admin@masterygrid.demo",
            full_name="MasteryGrid Demo Admin",
            role=UserRole.SCHOOL_ADMIN,
            school=school,
        )
        teacher = self.ensure_user(
            email="teacher@masterygrid.demo",
            full_name="Adaora Okafor",
            role=UserRole.TEACHER,
            school=school,
        )
        students = [
            self.ensure_user(
                email="student1@masterygrid.demo",
                full_name="Chinedu Okeke",
                role=UserRole.STUDENT,
                school=school,
            ),
            self.ensure_user(
                email="student2@masterygrid.demo",
                full_name="Amina Bello",
                role=UserRole.STUDENT,
                school=school,
            ),
            self.ensure_user(
                email="student3@masterygrid.demo",
                full_name="Tunde Adeyemi",
                role=UserRole.STUDENT,
                school=school,
            ),
        ]

        self.ensure_teacher_profile(teacher, school)
        for index, student in enumerate(students, start=1):
            self.ensure_student_profile(student, school, index)

        session, term = self.ensure_session_and_term(school)
        class_level, class_arm, subject, topics = self.ensure_academics(school)
        teacher_assignment = self.ensure_teacher_assignment(
            school=school,
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            session=session,
            term=term,
        )
        enrollments = [
            self.ensure_student_enrollment(
                school=school,
                student=student,
                class_arm=class_arm,
                session=session,
                term=term,
            )
            for student in students
        ]
        source = self.ensure_question_source()
        questions = self.ensure_questions(
            school=school,
            subject=subject,
            class_level=class_level,
            topics=topics,
            source=source,
            admin=admin,
            teacher=teacher,
        )
        lesson_log = self.ensure_lesson_log(
            school=school,
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            topic=topics["Quadratic Equations"],
            session=session,
            term=term,
        )
        assignment = self.ensure_assignment(
            school=school,
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            topic=topics["Quadratic Equations"],
            lesson_log=lesson_log,
            quadratic_questions=questions["Quadratic Equations"],
        )

        return {
            "school": school,
            "admin": admin,
            "teacher": teacher,
            "students": students,
            "session": session,
            "term": term,
            "class_level": class_level,
            "class_arm": class_arm,
            "subject": subject,
            "topics": topics,
            "teacher_assignment": teacher_assignment,
            "enrollments": enrollments,
            "source": source,
            "questions": questions,
            "lesson_log": lesson_log,
            "assignment": assignment,
        }

    def ensure_user(self, *, email, full_name, role, school):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "role": role,
                "school": school,
                "is_active": True,
            },
        )
        user.full_name = full_name
        user.role = role
        user.school = school
        user.is_active = True
        user.set_password(DEMO_PASSWORD)
        self.save_clean(user)
        self.note("users", created)
        return user

    def ensure_teacher_profile(self, teacher, school):
        profile, created = TeacherProfile.objects.update_or_create(
            user=teacher,
            defaults={
                "school": school,
                "staff_id": "TCH-001",
                "phone_number": "+2348090000001",
            },
        )
        self.save_clean(profile)
        self.note("profiles", created)
        return profile

    def ensure_student_profile(self, student, school, index):
        admission_number = f"STD-00{index}"
        profile, created = StudentProfile.objects.update_or_create(
            user=student,
            defaults={
                "school": school,
                "admission_number": admission_number,
                "guardian_name": f"Guardian {index}",
                "guardian_phone": f"+234809000000{index + 1}",
            },
        )
        self.save_clean(profile)
        self.note("profiles", created)
        return profile

    def ensure_session_and_term(self, school):
        AcademicSession.objects.filter(school=school, is_active=True).exclude(
            name="2025/2026",
        ).update(is_active=False)
        session, created = AcademicSession.objects.update_or_create(
            school=school,
            name="2025/2026",
            defaults={
                "starts_at": date(2025, 9, 1),
                "ends_at": date(2026, 7, 31),
                "is_active": True,
            },
        )
        self.save_clean(session)
        self.note("academic data", created)

        Term.objects.filter(school=school, is_active=True).exclude(
            academic_session=session,
            name=TermName.FIRST,
        ).update(is_active=False)
        term, created = Term.objects.update_or_create(
            school=school,
            academic_session=session,
            name=TermName.FIRST,
            defaults={
                "starts_at": date(2025, 9, 8),
                "ends_at": date(2025, 12, 12),
                "is_active": True,
            },
        )
        self.save_clean(term)
        self.note("academic data", created)
        return session, term

    def ensure_academics(self, school):
        class_level, created = ClassLevel.objects.update_or_create(
            school=school,
            name="SS2",
            defaults={
                "description": "Senior Secondary School 2",
                "is_active": True,
            },
        )
        self.save_clean(class_level)
        self.note("academic data", created)

        class_arm, created = ClassArm.objects.update_or_create(
            school=school,
            class_level=class_level,
            name="Science A",
            defaults={
                "description": "SS2 Science A",
                "is_active": True,
            },
        )
        self.save_clean(class_arm)
        self.note("academic data", created)

        subject, created = Subject.objects.update_or_create(
            school=school,
            name="Mathematics",
            defaults={
                "code": "MTH",
                "description": "Senior secondary Mathematics",
                "is_jamb_subject": True,
                "is_active": True,
            },
        )
        self.save_clean(subject)
        self.note("academic data", created)

        topics = {}
        for title in ["Quadratic Equations", "Simultaneous Equations", "Logarithms"]:
            topic, created = Topic.objects.update_or_create(
                school=school,
                subject=subject,
                class_level=class_level,
                title=title,
                defaults={
                    "description": f"Demo Mathematics topic: {title}",
                    "curriculum_tags": ["SS2", "Mathematics", "JAMB"],
                    "jamb_relevance_level": "high",
                    "is_active": True,
                },
            )
            self.save_clean(topic)
            self.note("academic data", created)
            topics[title] = topic

        return class_level, class_arm, subject, topics

    def ensure_teacher_assignment(self, *, school, teacher, class_arm, subject, session, term):
        teacher_assignment, created = TeacherClassSubjectAssignment.objects.update_or_create(
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            academic_session=session,
            term=term,
            defaults={
                "school": school,
                "is_active": True,
            },
        )
        self.save_clean(teacher_assignment)
        self.note("teacher assignment", created)
        return teacher_assignment

    def ensure_student_enrollment(self, *, school, student, class_arm, session, term):
        enrollment, created = StudentEnrollment.objects.update_or_create(
            student=student,
            academic_session=session,
            term=term,
            defaults={
                "school": school,
                "class_arm": class_arm,
                "is_active": True,
            },
        )
        self.save_clean(enrollment)
        self.note("student enrollments", created)
        return enrollment

    def ensure_question_source(self):
        source, created = QuestionSource.objects.update_or_create(
            name="JAMB Mathematics Demo Questions",
            source_type=QuestionSourceType.JAMB_PAST_QUESTION,
            year=2024,
            defaults={
                "exam_body": "JAMB",
                "description": "Curated demo questions for MasteryGrid pilot testing.",
                "is_active": True,
            },
        )
        self.save_clean(source)
        self.note("question source", created)
        return source

    def ensure_questions(self, *, school, subject, class_level, topics, source, admin, teacher):
        by_topic = defaultdict(list)
        for spec in QUESTION_SPECS:
            topic = topics[spec["topic"]]
            question, created = Question.objects.update_or_create(
                school=school,
                subject=subject,
                topic=topic,
                class_level=class_level,
                question_text=spec["text"],
                defaults={
                    "source": source,
                    "explanation": spec["explanation"],
                    "difficulty": spec["difficulty"],
                    "status": QuestionStatus.APPROVED,
                    "created_by": teacher,
                    "reviewed_by": admin,
                    "reviewed_at": timezone.now(),
                    "is_active": True,
                },
            )
            self.save_clean(question)
            self.ensure_question_options(question, spec["options"])
            validate_persisted_question_options(question)
            self.note("questions", created)
            by_topic[spec["topic"]].append(question)

        for topic_questions in by_topic.values():
            topic_questions.sort(key=lambda item: item.question_text)

        return dict(by_topic)

    def ensure_question_options(self, question, option_specs):
        for label, text, _is_correct in option_specs:
            option, _created = QuestionOption.objects.update_or_create(
                question=question,
                label=label,
                defaults={
                    "text": text,
                    "is_correct": False,
                },
            )
            self.save_clean(option)

        for label, text, is_correct in option_specs:
            option = QuestionOption.objects.get(question=question, label=label)
            option.text = text
            option.is_correct = is_correct
            self.save_clean(option, update_fields=["text", "is_correct", "updated_at"])

    def ensure_lesson_log(self, *, school, teacher, class_arm, subject, topic, session, term):
        lesson_log, created = LessonLog.objects.update_or_create(
            school=school,
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            topic=topic,
            academic_session=session,
            term=term,
            taught_at=aware_datetime(2026, 5, 1, 9, 0),
            defaults={
                "notes": "Introduced factorisation and root-finding methods for quadratic equations.",
            },
        )
        self.save_clean(lesson_log)
        self.note("lesson logs", created)
        return lesson_log

    def ensure_assignment(
        self,
        *,
        school,
        teacher,
        class_arm,
        subject,
        topic,
        lesson_log,
        quadratic_questions,
    ):
        now = timezone.now()
        assignment, created = Assignment.objects.update_or_create(
            school=school,
            teacher=teacher,
            class_arm=class_arm,
            subject=subject,
            topic=topic,
            title="Quadratic Equations Practice",
            defaults={
                "lesson_log": lesson_log,
                "instructions": "Answer all questions. Choose the best option for each question.",
                "question_count": 5,
                "duration_minutes": 30,
                "starts_at": now - timedelta(days=1),
                "due_at": now + timedelta(days=14),
                "status": AssignmentStatus.PUBLISHED,
                "published_at": now,
            },
        )
        self.save_clean(assignment)
        self.ensure_assignment_questions(assignment, quadratic_questions[:5])
        self.note("assignment", created)
        return assignment

    def ensure_assignment_questions(self, assignment, selected_questions):
        if assignment.submissions.exists():
            existing_count = assignment.assignment_questions.count()
            if existing_count != len(selected_questions):
                self.stdout.write(
                    self.style.WARNING(
                        "Kept existing assignment questions because submissions already exist."
                    )
                )
            return

        assignment.assignment_questions.all().delete()
        for order, question in enumerate(selected_questions, start=1):
            assignment_question = AssignmentQuestion(
                assignment=assignment,
                question=question,
                order=order,
                marks=1,
            )
            self.save_clean(assignment_question)

    def seed_submissions(self, context):
        assignment = context["assignment"]
        assignment_questions = list(
            assignment.assignment_questions.select_related("question").order_by("order")
        )
        score_plan = [
            (context["students"][0], 5, 12),
            (context["students"][1], 3, 18),
            (context["students"][2], 1, 24),
        ]

        for student, correct_count, minutes_spent in score_plan:
            self.ensure_submission(
                assignment=assignment,
                student=student,
                assignment_questions=assignment_questions,
                correct_count=correct_count,
                minutes_spent=minutes_spent,
            )

    def ensure_submission(
        self,
        *,
        assignment,
        student,
        assignment_questions,
        correct_count,
        minutes_spent,
    ):
        now = timezone.now()
        total_marks = sum(item.marks for item in assignment_questions)
        score = min(correct_count, len(assignment_questions))
        percentage = Decimal("0.00")
        if total_marks:
            percentage = (
                Decimal(score) / Decimal(total_marks) * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        submission, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "school": assignment.school,
                "status": SubmissionStatus.GRADED,
            },
        )
        submitted_at = now - timedelta(hours=3, minutes=minutes_spent)
        submission.school = assignment.school
        submission.status = SubmissionStatus.GRADED
        submission.started_at = submitted_at - timedelta(minutes=minutes_spent)
        submission.submitted_at = submitted_at
        submission.graded_at = submitted_at + timedelta(minutes=1)
        submission.score = score
        submission.total_marks = total_marks
        submission.percentage = percentage
        submission.time_spent_seconds = minutes_spent * 60
        submission.question_order = [item.id for item in assignment_questions]
        self.save_clean(submission)

        StudentAnswer.objects.filter(submission=submission).exclude(
            assignment_question__in=assignment_questions,
        ).delete()

        for index, assignment_question in enumerate(assignment_questions):
            selected_option = self.pick_option(
                assignment_question=assignment_question,
                should_be_correct=index < correct_count,
            )
            is_correct = bool(selected_option.is_correct)
            answer, _answer_created = StudentAnswer.objects.update_or_create(
                submission=submission,
                assignment_question=assignment_question,
                defaults={
                    "selected_option": selected_option,
                    "is_correct": is_correct,
                    "marks_awarded": assignment_question.marks if is_correct else 0,
                    "answered_at": submission.submitted_at,
                },
            )
            self.save_clean(answer)

        self.note("submissions", created)
        return submission

    def pick_option(self, *, assignment_question, should_be_correct):
        options = list(assignment_question.question.options.order_by("label"))
        if should_be_correct:
            return next(option for option in options if option.is_correct)
        return next(option for option in options if not option.is_correct)

    def print_summary(self, *, with_submissions):
        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))
        for section in [
            "school",
            "users",
            "profiles",
            "academic data",
            "teacher assignment",
            "student enrollments",
            "question source",
            "questions",
            "lesson logs",
            "assignment",
        ]:
            counts = self.summary[section]
            self.stdout.write(
                f"- {section}: {counts['created']} created, {counts['found']} found/updated"
            )

        if with_submissions:
            counts = self.summary["submissions"]
            self.stdout.write(
                f"- submissions: {counts['created']} created, {counts['found']} found/updated"
            )

        self.stdout.write("")
        self.stdout.write("Demo login credentials:")
        self.stdout.write(f"- School admin: admin@masterygrid.demo / {DEMO_PASSWORD}")
        self.stdout.write(f"- Teacher: teacher@masterygrid.demo / {DEMO_PASSWORD}")
        self.stdout.write(f"- Student 1: student1@masterygrid.demo / {DEMO_PASSWORD}")
        self.stdout.write(f"- Student 2: student2@masterygrid.demo / {DEMO_PASSWORD}")
        self.stdout.write(f"- Student 3: student3@masterygrid.demo / {DEMO_PASSWORD}")
