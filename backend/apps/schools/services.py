"""School business workflows."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q

from apps.academics.models import (
    AcademicSession,
    ClassArm,
    ClassLevel,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
from apps.accounts.models import User
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question
from apps.schools.models import School


SETUP_STEPS = [
    {
        "key": "academic_session",
        "label": "Academic session",
        "description": "Create and activate the current school year.",
        "action_url": "/admin/academic-sessions",
        "recommendation": "Add the current academic session and mark it active.",
    },
    {
        "key": "term",
        "label": "Term",
        "description": "Create and activate the current term.",
        "action_url": "/admin/terms",
        "recommendation": "Add the current term under the active academic session.",
    },
    {
        "key": "class_levels",
        "label": "Class levels",
        "description": "Set up levels such as JSS1, SS2, or JAMB.",
        "action_url": "/admin/class-levels",
        "recommendation": "Add at least one class level for your school.",
    },
    {
        "key": "class_arms",
        "label": "Class arms",
        "description": "Set up class arms for learners, such as SS2 Science A.",
        "action_url": "/admin/class-arms",
        "recommendation": "Add at least one class arm linked to a class level.",
    },
    {
        "key": "subjects",
        "label": "Subjects",
        "description": "Create the subjects taught in this school.",
        "action_url": "/admin/subjects",
        "recommendation": "Add at least one active subject.",
    },
    {
        "key": "topics",
        "label": "Topics",
        "description": "Add curriculum topics under subjects and class levels.",
        "action_url": "/admin/topics",
        "recommendation": "Add at least one topic for an active subject and class level.",
    },
    {
        "key": "teachers",
        "label": "Teachers",
        "description": "Create or import teacher accounts.",
        "action_url": "/admin/teachers",
        "recommendation": "Add at least one active teacher.",
    },
    {
        "key": "students",
        "label": "Students",
        "description": "Create or import student accounts.",
        "action_url": "/admin/students",
        "recommendation": "Add at least one active student.",
    },
    {
        "key": "teacher_assignments",
        "label": "Teacher assignments",
        "description": "Assign teachers to class arms and subjects.",
        "action_url": "/admin/teacher-assignments",
        "recommendation": "Assign at least one teacher to a class arm and subject.",
    },
    {
        "key": "student_enrollments",
        "label": "Student enrollments",
        "description": "Enroll students into the active class/session.",
        "action_url": "/admin/student-enrollments",
        "recommendation": "Enroll at least one student into a class arm.",
    },
    {
        "key": "question_bank",
        "label": "Question bank",
        "description": "Import or approve questions for assignments and practice.",
        "action_url": "/admin/question-bank/imports/new",
        "recommendation": "Import, review, and approve at least one active question.",
    },
]


def resolve_setup_school(user, school_id=None):
    if getattr(user, "role", None) == UserRole.SCHOOL_ADMIN:
        if not user.school_id:
            raise PermissionDenied("School admin account is not linked to a school.")
        return user.school

    if getattr(user, "role", None) == UserRole.PLATFORM_ADMIN or getattr(
        user, "is_superuser", False
    ):
        if not school_id:
            if user.school_id:
                return user.school
            raise ValidationError({"school": "school query parameter is required."})
        try:
            return School.objects.get(id=school_id)
        except (School.DoesNotExist, ValueError, TypeError):
            raise ValidationError({"school": "Selected school was not found."})

    raise PermissionDenied("You do not have permission to view school setup status.")


def setup_counts_for_school(school):
    school_subjects = Subject.objects.filter(school=school, is_active=True)
    return {
        "academic_session": AcademicSession.objects.filter(
            school=school,
            is_active=True,
        ).count(),
        "term": Term.objects.filter(school=school, is_active=True).count(),
        "class_levels": ClassLevel.objects.filter(school=school).count(),
        "class_arms": ClassArm.objects.filter(school=school).count(),
        "subjects": school_subjects.count(),
        "topics": Topic.objects.filter(school=school).count(),
        "teachers": User.objects.filter(
            school=school,
            role=UserRole.TEACHER,
            is_active=True,
        ).count(),
        "students": User.objects.filter(
            school=school,
            role=UserRole.STUDENT,
            is_active=True,
        ).count(),
        "teacher_assignments": TeacherClassSubjectAssignment.objects.filter(
            school=school,
            is_active=True,
        ).count(),
        "student_enrollments": StudentEnrollment.objects.filter(
            school=school,
            is_active=True,
        ).count(),
        "question_bank": Question.objects.filter(
            Q(school=school) | Q(school__isnull=True),
            status=QuestionStatus.APPROVED,
            is_active=True,
        ).count(),
    }


def step_status(count, required_count=1):
    return "complete" if count >= required_count else "incomplete"


def build_setup_steps(counts):
    steps = []
    for definition in SETUP_STEPS:
        count = counts[definition["key"]]
        steps.append(
            {
                **definition,
                "status": step_status(count),
                "count": count,
                "required_count": 1,
            }
        )
    return steps


def setup_warnings(steps):
    completed_by_key = {step["key"]: step["status"] == "complete" for step in steps}
    warnings = []
    if completed_by_key["term"] and not completed_by_key["academic_session"]:
        warnings.append("An active term exists, but no active academic session was found.")
    if completed_by_key["class_arms"] and not completed_by_key["class_levels"]:
        warnings.append("Class arms exist, but no class level was found.")
    if completed_by_key["topics"] and not completed_by_key["subjects"]:
        warnings.append("Topics exist, but no active school subject was found.")
    if completed_by_key["teacher_assignments"] and not completed_by_key["teachers"]:
        warnings.append("Teacher assignments exist, but no active teacher was found.")
    if completed_by_key["student_enrollments"] and not completed_by_key["students"]:
        warnings.append("Student enrollments exist, but no active student was found.")
    return warnings


def get_school_setup_status(user, school_id=None):
    school = resolve_setup_school(user, school_id=school_id)
    counts = setup_counts_for_school(school)
    steps = build_setup_steps(counts)
    complete_count = sum(1 for step in steps if step["status"] == "complete")
    completion_percentage = round((complete_count / len(steps)) * 100)
    next_step = next((step for step in steps if step["status"] != "complete"), None)
    warnings = setup_warnings(steps)

    return {
        "school_id": school.id,
        "school_name": school.name,
        "completion_percentage": completion_percentage,
        "is_setup_complete": complete_count == len(steps),
        "steps": steps,
        "next_step": next_step,
        "blocking_issues": [
            step["recommendation"]
            for step in steps
            if step["status"] == "incomplete"
        ],
        "warnings": warnings,
    }
