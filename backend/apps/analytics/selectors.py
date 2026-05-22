from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.academics.models import ClassArm, StudentEnrollment, Subject
from apps.assignments.models import Assignment
from apps.common.choices import AssignmentStatus, UserRole
from apps.schools.models import School
from apps.submissions.models import StudentAnswer, Submission

User = get_user_model()


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(user, "is_superuser", False)
        )
    )


def get_teacher_assignments(teacher):
    queryset = Assignment.objects.select_related(
        "school",
        "teacher",
        "class_arm",
        "class_arm__class_level",
        "subject",
        "topic",
    ).prefetch_related("assignment_questions")

    if is_platform_admin(teacher):
        return queryset

    if not teacher or not teacher.is_authenticated:
        return queryset.none()

    if teacher.role == UserRole.SCHOOL_ADMIN and teacher.school_id:
        return queryset.filter(school=teacher.school)

    if teacher.role == UserRole.TEACHER and teacher.school_id:
        return queryset.filter(school=teacher.school, teacher=teacher)

    return queryset.none()


def get_assignment_for_analytics(user, assignment_id):
    return get_object_or_404(get_teacher_assignments(user), pk=assignment_id)


def get_assignment_expected_students(assignment):
    return (
        User.objects.filter(
            role=UserRole.STUDENT,
            school=assignment.school,
            student_enrollments__school=assignment.school,
            student_enrollments__class_arm=assignment.class_arm,
            student_enrollments__is_active=True,
        )
        .select_related("student_profile")
        .distinct()
        .order_by("full_name", "email")
    )


def get_assignment_submissions(assignment):
    return Submission.objects.filter(
        school=assignment.school,
        assignment=assignment,
    ).select_related(
        "student",
        "student__student_profile",
        "assignment",
        "assignment__subject",
        "assignment__topic",
        "assignment__class_arm",
    ).prefetch_related(
        "answers",
        "answers__selected_option",
        "answers__assignment_question",
        "answers__assignment_question__question",
    )


def get_teacher_students(teacher):
    assignments = get_teacher_assignments(teacher)
    class_arm_ids = assignments.values("class_arm_id")
    school_filter = {}

    if teacher.role in {UserRole.TEACHER, UserRole.SCHOOL_ADMIN} and teacher.school_id:
        school_filter["school"] = teacher.school

    return (
        User.objects.filter(
            role=UserRole.STUDENT,
            student_enrollments__class_arm_id__in=class_arm_ids,
            student_enrollments__is_active=True,
            **school_filter,
        )
        .select_related("student_profile")
        .distinct()
        .order_by("full_name", "email")
    )


def get_teacher_student_submissions(teacher, student):
    assignments = get_teacher_assignments(teacher)
    return Submission.objects.filter(
        assignment__in=assignments,
        student=student,
    ).select_related(
        "assignment",
        "assignment__subject",
        "assignment__topic",
        "assignment__class_arm",
    ).prefetch_related("answers")


def get_question_performance_for_assignment(assignment):
    answers = (
        StudentAnswer.objects.filter(
            submission__assignment=assignment,
            submission__graded_at__isnull=False,
        )
        .select_related(
            "assignment_question",
            "assignment_question__question",
            "selected_option",
        )
        .order_by("assignment_question__order")
    )

    performance = {}
    for assignment_question in assignment.assignment_questions.select_related(
        "question"
    ).order_by("order"):
        performance[assignment_question.id] = {
            "assignment_question_id": assignment_question.id,
            "question_text": assignment_question.question.question_text,
            "total_attempts": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "correct_percentage": 0.0,
        }

    for answer in answers:
        item = performance.get(answer.assignment_question_id)
        if item is None:
            continue
        item["total_attempts"] += 1
        if answer.is_correct:
            item["correct_count"] += 1
        else:
            item["wrong_count"] += 1

    for item in performance.values():
        attempts = item["total_attempts"]
        if attempts:
            item["correct_percentage"] = round(
                item["correct_count"] / attempts * 100,
                2,
            )

    return list(performance.values())


def get_published_assignments_for_student_from_queryset(student, assignments):
    enrolled_class_arm_ids = StudentEnrollment.objects.filter(
        school=student.school,
        student=student,
        is_active=True,
    ).values("class_arm_id")

    return assignments.filter(
        Q(school=student.school),
        Q(class_arm_id__in=enrolled_class_arm_ids),
        Q(status=AssignmentStatus.PUBLISHED),
    )


def get_school_for_admin(user, school_id=None):
    if not user or not user.is_authenticated:
        return None

    if user.role == UserRole.SCHOOL_ADMIN:
        return user.school

    if is_platform_admin(user) and school_id:
        return get_object_or_404(School, pk=school_id)

    return None


def filter_queryset_by_school(queryset, school):
    if school is None:
        return queryset
    return queryset.filter(school=school)


def get_school_students(school):
    queryset = User.objects.filter(role=UserRole.STUDENT).select_related(
        "school",
        "student_profile",
    )
    return filter_queryset_by_school(queryset, school)


def get_school_teachers(school):
    queryset = User.objects.filter(role=UserRole.TEACHER).select_related(
        "school",
        "teacher_profile",
    )
    return filter_queryset_by_school(queryset, school)


def get_school_assignments(school):
    queryset = Assignment.objects.select_related(
        "school",
        "teacher",
        "teacher__teacher_profile",
        "class_arm",
        "class_arm__class_level",
        "subject",
        "topic",
    ).prefetch_related("submissions")
    return filter_queryset_by_school(queryset, school)


def get_school_submissions(school):
    queryset = Submission.objects.select_related(
        "school",
        "assignment",
        "assignment__teacher",
        "assignment__class_arm",
        "assignment__class_arm__class_level",
        "assignment__subject",
        "assignment__topic",
        "student",
        "student__student_profile",
    ).prefetch_related(
        "answers",
        "answers__assignment_question",
        "answers__assignment_question__question",
    )
    return filter_queryset_by_school(queryset, school)


def get_school_class_arms(school):
    queryset = ClassArm.objects.select_related("school", "class_level").filter(
        is_active=True,
    )
    return filter_queryset_by_school(queryset, school)


def get_school_subjects(school):
    queryset = Subject.objects.filter(is_active=True).select_related("school")
    if school is None:
        return queryset
    return queryset.filter(Q(school=school) | Q(school__isnull=True))
