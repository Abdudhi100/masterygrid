from collections import defaultdict
from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.academics.models import StudentEnrollment, TeacherClassSubjectAssignment
from apps.analytics.selectors import (
    get_assignment_expected_students,
    get_assignment_for_analytics,
    get_assignment_submissions,
    get_school_assignments,
    get_school_class_arms,
    get_school_for_admin,
    get_school_students,
    get_school_subjects,
    get_school_submissions,
    get_school_teachers,
    get_published_assignments_for_student_from_queryset,
    get_question_performance_for_assignment,
    get_teacher_assignments,
    get_teacher_student_submissions,
    get_teacher_students,
)
from apps.common.choices import AssignmentStatus, SubmissionStatus, UserRole
from apps.common.choices import QuestionStatus
from apps.practice.analytics import get_student_learning_path
from apps.practice.models import PracticeSession, PracticeSessionStatus
from apps.question_bank.models import Question
from apps.submissions.models import Submission


LOW_SCORE_THRESHOLD = 40
WEAK_TOPIC_THRESHOLD = 50
REMEDIATION_DEFAULT_LIMIT = 8
ADMIN_INTERVENTION_LIMIT = 10


RISK_LEVEL_WEIGHT = {
    "critical": 3,
    "high": 2,
    "moderate": 1,
    "low": 0,
}


def percentage_value(value):
    if value is None:
        return 0.0
    return round(float(value), 2)


def admission_number_for(student):
    profile = getattr(student, "student_profile", None)
    return getattr(profile, "admission_number", None)


def class_arm_name_for_student(student):
    enrollment = (
        student.student_enrollments.select_related(
            "class_arm",
            "class_arm__class_level",
        )
        .filter(is_active=True)
        .first()
    )
    return str(enrollment.class_arm) if enrollment else None


def get_teacher_overview(teacher):
    assignments = get_teacher_assignments(teacher)
    assignment_ids = assignments.values("id")
    submissions = Submission.objects.filter(assignment_id__in=assignment_ids)
    graded_submissions = submissions.filter(graded_at__isnull=False)

    recent_assignments = [
        {
            "id": assignment.id,
            "title": assignment.title,
            "subject": assignment.subject.name,
            "topic": assignment.topic.title,
            "class_arm": str(assignment.class_arm),
            "status": assignment.status,
            "due_at": assignment.due_at,
            "question_count": assignment.question_count,
            "created_at": assignment.created_at,
            "submission_count": assignment.submissions.count(),
        }
        for assignment in assignments.order_by("-created_at")[:5]
    ]

    seen_students = set()
    recent_low_performing_students = []
    low_submissions = (
        graded_submissions.filter(percentage__lt=LOW_SCORE_THRESHOLD)
        .select_related("student", "assignment", "assignment__topic")
        .order_by("-graded_at")
    )
    for submission in low_submissions:
        if submission.student_id in seen_students:
            continue
        seen_students.add(submission.student_id)
        recent_low_performing_students.append(
            {
                "student_id": submission.student_id,
                "student_name": submission.student.full_name,
                "assignment_id": submission.assignment_id,
                "assignment_title": submission.assignment.title,
                "topic": submission.assignment.topic.title,
                "percentage": percentage_value(submission.percentage),
                "graded_at": submission.graded_at,
            }
        )
        if len(recent_low_performing_students) == 5:
            break

    average_percentage = graded_submissions.aggregate(
        average=Avg("percentage"),
    )["average"]

    return {
        "total_assignments_created": assignments.count(),
        "published_assignments": assignments.filter(
            status=AssignmentStatus.PUBLISHED,
        ).count(),
        "draft_assignments": assignments.filter(status=AssignmentStatus.DRAFT).count(),
        "closed_assignments": assignments.filter(status=AssignmentStatus.CLOSED).count(),
        "total_submissions": submissions.count(),
        "graded_submissions": graded_submissions.count(),
        "pending_submissions": submissions.exclude(graded_at__isnull=False).count(),
        "average_score_percentage": percentage_value(average_percentage),
        "recent_assignments": recent_assignments,
        "recent_low_performing_students": recent_low_performing_students,
        "weak_topics_summary": get_teacher_weak_topics(teacher)[:5],
    }


def get_assignment_results(teacher, assignment_id):
    assignment = get_assignment_for_analytics(teacher, assignment_id)
    expected_students = list(get_assignment_expected_students(assignment))
    submissions = list(get_assignment_submissions(assignment))
    submissions_by_student_id = {submission.student_id: submission for submission in submissions}
    graded_submissions = [
        submission for submission in submissions if submission.graded_at is not None
    ]
    started_submissions = [
        submission for submission in submissions if submission.started_at is not None
    ]
    submitted_submissions = [
        submission
        for submission in submissions
        if submission.submitted_at is not None
        or submission.status
        in {
            SubmissionStatus.SUBMITTED,
            SubmissionStatus.GRADED,
            SubmissionStatus.AUTO_SUBMITTED,
        }
    ]

    student_results = []
    for student in expected_students:
        submission = submissions_by_student_id.get(student.id)
        student_results.append(
            {
                "student_id": student.id,
                "student_name": student.full_name,
                "admission_number": admission_number_for(student),
                "status": submission.status if submission else SubmissionStatus.NOT_STARTED,
                "score": submission.score if submission else 0,
                "total_marks": submission.total_marks if submission else 0,
                "percentage": percentage_value(submission.percentage) if submission else 0.0,
                "submitted_at": submission.submitted_at if submission else None,
                "time_spent_seconds": (
                    submission.time_spent_seconds if submission else None
                ),
            }
        )

    total_expected = len(expected_students)
    total_started = len(started_submissions)
    total_submitted = len(submitted_submissions)
    total_graded = len(graded_submissions)
    percentages = [float(submission.percentage) for submission in graded_submissions]
    average_percentage = (
        round(sum(percentages) / len(percentages), 2) if percentages else 0.0
    )
    question_performance = get_question_performance_for_assignment(assignment)

    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "subject": assignment.subject.name,
            "topic": assignment.topic.title,
            "class_arm": str(assignment.class_arm),
            "status": assignment.status,
            "question_count": assignment.question_count,
            "due_at": assignment.due_at,
        },
        "submission_summary": {
            "total_students_expected": total_expected,
            "total_started": total_started,
            "total_submitted": total_submitted,
            "total_graded": total_graded,
            "total_not_started": max(total_expected - total_started, 0),
            "submission_rate": (
                round(total_submitted / total_expected * 100, 2)
                if total_expected
                else 0.0
            ),
            "average_percentage": average_percentage,
            "highest_percentage": round(max(percentages), 2) if percentages else 0.0,
            "lowest_percentage": round(min(percentages), 2) if percentages else 0.0,
        },
        "student_results": student_results,
        "question_performance": question_performance,
        "most_missed_questions": sorted(
            question_performance,
            key=lambda item: (item["wrong_count"], -item["correct_percentage"]),
            reverse=True,
        )[:5],
    }


def get_teacher_weak_students(teacher):
    assignments = get_teacher_assignments(teacher)
    students = get_teacher_students(teacher)
    weak_students = []

    for student in students:
        submissions = list(get_teacher_student_submissions(teacher, student))
        graded_submissions = [
            submission for submission in submissions if submission.graded_at is not None
        ]
        percentages = [float(submission.percentage) for submission in graded_submissions]
        average_percentage = (
            round(sum(percentages) / len(percentages), 2) if percentages else 0.0
        )
        below_40_count = sum(1 for value in percentages if value < LOW_SCORE_THRESHOLD)
        missed_assignment_count = get_missed_assignment_count(assignments, student, submissions)
        weak_topics = get_student_weak_topics_from_submissions(graded_submissions)

        is_weak = (
            (graded_submissions and average_percentage < LOW_SCORE_THRESHOLD)
            or below_40_count >= 2
            or missed_assignment_count >= 2
        )
        if not is_weak:
            continue

        risk_level = calculate_risk_level(
            average_percentage=average_percentage,
            missed_assignment_count=missed_assignment_count,
            weak_topics=weak_topics,
        )
        weak_students.append(
            {
                "student_id": student.id,
                "student_name": student.full_name,
                "class_arm": class_arm_name_for_student(student),
                "average_percentage": average_percentage,
                "graded_submission_count": len(graded_submissions),
                "missed_assignment_count": missed_assignment_count,
                "weak_topics": weak_topics,
                "risk_level": risk_level,
                "recommendation": generate_recommendation(
                    risk_level=risk_level,
                    average_percentage=average_percentage,
                    missed_assignment_count=missed_assignment_count,
                    weak_topics=weak_topics,
                ),
            }
        )

    return sorted(
        weak_students,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["risk_level"]],
            item["average_percentage"],
            -item["missed_assignment_count"],
        ),
    )


def get_teacher_weak_topics(teacher):
    assignments = get_teacher_assignments(teacher)
    topic_groups = {}

    for assignment in assignments.select_related("subject", "topic", "class_arm"):
        submissions = list(
            assignment.submissions.filter(graded_at__isnull=False).select_related(
                "student",
            )
        )
        if not submissions:
            continue

        key = (assignment.subject_id, assignment.topic_id, assignment.class_arm_id)
        item = topic_groups.setdefault(
            key,
            {
                "subject": assignment.subject.name,
                "topic": assignment.topic.title,
                "class_arm": str(assignment.class_arm),
                "percentages": [],
                "student_percentages": defaultdict(list),
            },
        )
        for submission in submissions:
            percentage = float(submission.percentage)
            item["percentages"].append(percentage)
            item["student_percentages"][submission.student_id].append(percentage)

    weak_topics = []
    for item in topic_groups.values():
        average_percentage = round(
            sum(item["percentages"]) / len(item["percentages"]),
            2,
        )
        weak_student_count = sum(
            1
            for scores in item["student_percentages"].values()
            if sum(scores) / len(scores) < WEAK_TOPIC_THRESHOLD
        )
        if average_percentage >= WEAK_TOPIC_THRESHOLD and weak_student_count == 0:
            continue

        weak_topics.append(
            {
                "subject": item["subject"],
                "topic": item["topic"],
                "class_arm": item["class_arm"],
                "average_percentage": average_percentage,
                "total_submissions": len(item["percentages"]),
                "weak_student_count": weak_student_count,
                "recommendation": (
                    "Schedule a short reteach and assign follow-up practice for this topic."
                    if average_percentage < WEAK_TOPIC_THRESHOLD
                    else "Give targeted support to the weak students on this topic."
                ),
            }
        )

    return sorted(weak_topics, key=lambda item: item["average_percentage"])


def _approved_question_counts_for_teacher_remediation(teacher):
    if not teacher or not teacher.school_id:
        return {}

    rows = (
        Question.objects.filter(
            Q(school__isnull=True) | Q(school=teacher.school),
            status=QuestionStatus.APPROVED,
            is_active=True,
            topic__isnull=False,
            class_level__isnull=False,
        )
        .values("subject_id", "topic_id", "class_level_id")
        .annotate(available_approved_questions=Count("id"))
    )
    return {
        (row["subject_id"], row["topic_id"], row["class_level_id"]): row[
            "available_approved_questions"
        ]
        for row in rows
    }


def _recommended_remediation_question_count(available_count):
    return max(1, min(10, available_count))


def _remediation_priority(average_score, weak_student_count, available_count):
    if average_score < LOW_SCORE_THRESHOLD or weak_student_count >= 3:
        return "high" if available_count else "medium"
    if average_score < WEAK_TOPIC_THRESHOLD or weak_student_count >= 1:
        return "medium" if available_count else "low"
    return "low"


def _remediation_action_text(average_score, weak_student_count, available_count):
    if not available_count:
        return (
            "Approve more question-bank questions for this topic before creating "
            "a remedial assignment."
        )
    if average_score < LOW_SCORE_THRESHOLD:
        return (
            "Create a short remedial assignment and reteach the core method before "
            "students attempt it."
        )
    if weak_student_count:
        return (
            "Create targeted follow-up practice for the students struggling with "
            "this topic."
        )
    return "Create a brief revision assignment to strengthen this topic."


def _remediation_sort_key(card):
    latest_value = card["latest_assignment_created_at"]
    latest_timestamp = latest_value.timestamp() if latest_value else 0
    has_questions_rank = 0 if card["available_approved_questions"] > 0 else 1
    return (
        has_questions_rank,
        card["average_score"],
        -card["weak_student_count"],
        -card["available_approved_questions"],
        -latest_timestamp,
    )


def get_teacher_remediation_plan(teacher, limit=REMEDIATION_DEFAULT_LIMIT):
    assignments = get_teacher_assignments(teacher).select_related(
        "subject",
        "topic",
        "class_arm",
        "class_arm__class_level",
    )
    availability = _approved_question_counts_for_teacher_remediation(teacher)
    topic_groups = {}
    total_graded_submissions = 0

    for assignment in assignments:
        submissions = list(
            assignment.submissions.filter(graded_at__isnull=False).select_related(
                "student",
                "student__student_profile",
            )
        )
        if not submissions:
            continue

        total_graded_submissions += len(submissions)
        key = (assignment.subject_id, assignment.topic_id, assignment.class_arm_id)
        item = topic_groups.setdefault(
            key,
            {
                "subject_id": assignment.subject_id,
                "subject_name": assignment.subject.name,
                "topic_id": assignment.topic_id,
                "topic_title": assignment.topic.title,
                "class_arm_id": assignment.class_arm_id,
                "class_arm_name": str(assignment.class_arm),
                "class_level_id": assignment.class_arm.class_level_id,
                "class_level_name": assignment.class_arm.class_level.name,
                "percentages": [],
                "student_percentages": defaultdict(list),
                "students": {},
                "latest_assignment_id": assignment.id,
                "latest_assignment_title": assignment.title,
                "latest_assignment_created_at": assignment.created_at,
            },
        )

        if assignment.created_at > item["latest_assignment_created_at"]:
            item["latest_assignment_id"] = assignment.id
            item["latest_assignment_title"] = assignment.title
            item["latest_assignment_created_at"] = assignment.created_at

        for submission in submissions:
            percentage = float(submission.percentage)
            item["percentages"].append(percentage)
            item["student_percentages"][submission.student_id].append(percentage)
            item["students"][submission.student_id] = submission.student

    weak_topic_cards = []
    affected_students_by_id = {}
    for item in topic_groups.values():
        average_score = round(
            sum(item["percentages"]) / len(item["percentages"]),
            2,
        )
        affected_students = []
        for student_id, scores in item["student_percentages"].items():
            student_average = round(sum(scores) / len(scores), 2)
            if student_average >= WEAK_TOPIC_THRESHOLD:
                continue
            student = item["students"][student_id]
            affected_student = {
                "student_id": student.id,
                "student_name": student.full_name,
                "admission_number": admission_number_for(student),
                "class_arm": item["class_arm_name"],
                "topic_id": item["topic_id"],
                "topic_title": item["topic_title"],
                "average_score": student_average,
                "attempted_count": len(scores),
            }
            affected_students.append(affected_student)
            existing_student = affected_students_by_id.get(student.id)
            if (
                existing_student is None
                or student_average < existing_student["average_score"]
            ):
                affected_students_by_id[student.id] = affected_student

        if average_score >= WEAK_TOPIC_THRESHOLD and not affected_students:
            continue

        available_count = availability.get(
            (
                item["subject_id"],
                item["topic_id"],
                item["class_level_id"],
            ),
            0,
        )
        recommended_question_count = (
            _recommended_remediation_question_count(available_count)
            if available_count
            else 0
        )
        suggested_assignment_title = f"Remedial: {item['topic_title']}"
        suggested_instructions = (
            f"Review {item['topic_title']} carefully. This remedial assignment "
            "focuses on common mistakes from recent class performance."
        )
        priority = _remediation_priority(
            average_score,
            len(affected_students),
            available_count,
        )
        recommended_action = _remediation_action_text(
            average_score,
            len(affected_students),
            available_count,
        )

        weak_topic_cards.append(
            {
                "subject_id": item["subject_id"],
                "subject": item["subject_name"],
                "topic_id": item["topic_id"],
                "topic": item["topic_title"],
                "class_arm_id": item["class_arm_id"],
                "class_arm": item["class_arm_name"],
                "class_level_id": item["class_level_id"],
                "class_level": item["class_level_name"],
                "average_score": average_score,
                "attempted_count": len(item["percentages"]),
                "weak_student_count": len(affected_students),
                "available_approved_questions": available_count,
                "recommended_question_count": recommended_question_count,
                "suggested_assignment_title": suggested_assignment_title,
                "suggested_instructions": suggested_instructions,
                "recommended_action": recommended_action,
                "priority": priority,
                "latest_assignment_id": item["latest_assignment_id"],
                "latest_assignment_title": item["latest_assignment_title"],
                "latest_assignment_created_at": item["latest_assignment_created_at"],
                "affected_students": sorted(
                    affected_students,
                    key=lambda student: (
                        student["average_score"],
                        student["student_name"],
                    ),
                ),
                "action_payload": {
                    "class_arm": item["class_arm_id"],
                    "subject": item["subject_id"],
                    "topic": item["topic_id"],
                    "question_count": recommended_question_count,
                    "title": suggested_assignment_title,
                    "instructions": suggested_instructions,
                    "remedial": True,
                },
            }
        )

    weak_topic_cards = sorted(weak_topic_cards, key=_remediation_sort_key)
    recommended_actions = [
        card
        for card in weak_topic_cards
        if card["available_approved_questions"] > 0
    ][:limit]
    limited_weak_topic_cards = weak_topic_cards[:limit]
    average_score = (
        round(
            sum(card["average_score"] * card["attempted_count"] for card in weak_topic_cards)
            / sum(card["attempted_count"] for card in weak_topic_cards),
            2,
        )
        if weak_topic_cards
        else 0.0
    )

    if not total_graded_submissions:
        message = "No graded submissions yet. Remediation will appear after students submit assignments."
    elif weak_topic_cards and not recommended_actions:
        message = "Weak topics were found, but more approved questions are needed before creating remedial assignments."
    elif not weak_topic_cards:
        message = "No weak topics detected yet."
    else:
        message = "Create remedial assignments for the highest-priority weak topics."

    return {
        "summary": {
            "total_weak_topics": len(weak_topic_cards),
            "actionable_topic_count": len(recommended_actions),
            "total_affected_students": len(affected_students_by_id),
            "total_graded_submissions": total_graded_submissions,
            "average_score": average_score,
            "message": message,
        },
        "recommended_actions": recommended_actions,
        "weak_topic_cards": limited_weak_topic_cards,
        "affected_students": sorted(
            affected_students_by_id.values(),
            key=lambda student: (student["average_score"], student["student_name"]),
        )[:20],
    }


def get_student_performance_for_teacher(teacher, student_id):
    student = get_object_or_404(get_teacher_students(teacher), pk=student_id)
    assignments = get_teacher_assignments(teacher)
    submissions = list(get_teacher_student_submissions(teacher, student))
    graded_submissions = [
        submission for submission in submissions if submission.graded_at is not None
    ]
    percentages = [float(submission.percentage) for submission in graded_submissions]
    average_percentage = (
        round(sum(percentages) / len(percentages), 2) if percentages else 0.0
    )
    missed_assignments = get_missed_assignments(assignments, student, submissions)
    performance_by_subject = group_student_performance(graded_submissions, "subject")
    performance_by_topic = group_student_performance(graded_submissions, "topic")
    weak_topics = [
        item for item in performance_by_topic if item["average_percentage"] < WEAK_TOPIC_THRESHOLD
    ]
    risk_level = calculate_risk_level(
        average_percentage=average_percentage,
        missed_assignment_count=len(missed_assignments),
        weak_topics=weak_topics,
    )

    return {
        "student": {
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "admission_number": admission_number_for(student),
            "class_arm": class_arm_name_for_student(student),
        },
        "assignments_attempted": len(graded_submissions),
        "average_percentage": average_percentage,
        "performance_by_subject": performance_by_subject,
        "performance_by_topic": performance_by_topic,
        "recent_scores": [
            {
                "assignment_id": submission.assignment_id,
                "assignment_title": submission.assignment.title,
                "subject": submission.assignment.subject.name,
                "topic": submission.assignment.topic.title,
                "score": submission.score,
                "total_marks": submission.total_marks,
                "percentage": percentage_value(submission.percentage),
                "graded_at": submission.graded_at,
            }
            for submission in sorted(
                graded_submissions,
                key=lambda item: item.graded_at or item.updated_at,
                reverse=True,
            )[:10]
        ],
        "weak_topics": weak_topics,
        "missed_assignments": missed_assignments,
        "recommendation": generate_recommendation(
            risk_level=risk_level,
            average_percentage=average_percentage,
            missed_assignment_count=len(missed_assignments),
            weak_topics=weak_topics,
        ),
    }


def get_missed_assignment_count(assignments, student, submissions):
    return len(get_missed_assignments(assignments, student, submissions))


def get_missed_assignments(assignments, student, submissions):
    submitted_assignment_ids = {
        submission.assignment_id
        for submission in submissions
        if submission.submitted_at is not None or submission.graded_at is not None
    }
    expected_assignments = get_published_assignments_for_student_from_queryset(
        student,
        assignments,
    )

    return [
        {
            "assignment_id": assignment.id,
            "title": assignment.title,
            "subject": assignment.subject.name,
            "topic": assignment.topic.title,
            "due_at": assignment.due_at,
        }
        for assignment in expected_assignments.select_related("subject", "topic")
        if assignment.id not in submitted_assignment_ids
    ]


def get_student_weak_topics_from_submissions(graded_submissions):
    grouped = defaultdict(list)
    metadata = {}
    for submission in graded_submissions:
        key = (submission.assignment.subject_id, submission.assignment.topic_id)
        grouped[key].append(float(submission.percentage))
        metadata[key] = {
            "subject": submission.assignment.subject.name,
            "topic": submission.assignment.topic.title,
        }

    weak_topics = []
    for key, scores in grouped.items():
        average_percentage = round(sum(scores) / len(scores), 2)
        if average_percentage < WEAK_TOPIC_THRESHOLD:
            weak_topics.append(
                {
                    **metadata[key],
                    "average_percentage": average_percentage,
                    "submission_count": len(scores),
                }
            )
    return sorted(weak_topics, key=lambda item: item["average_percentage"])


def group_student_performance(graded_submissions, group_type):
    grouped = defaultdict(list)
    labels = {}

    for submission in graded_submissions:
        if group_type == "subject":
            key = submission.assignment.subject_id
            labels[key] = submission.assignment.subject.name
        else:
            key = submission.assignment.topic_id
            labels[key] = submission.assignment.topic.title
        grouped[key].append(float(submission.percentage))

    return [
        {
            group_type: labels[key],
            "average_percentage": round(sum(scores) / len(scores), 2),
            "graded_submission_count": len(scores),
        }
        for key, scores in grouped.items()
    ]


def calculate_risk_level(*, average_percentage, missed_assignment_count, weak_topics):
    if average_percentage < 30 or missed_assignment_count >= 3:
        return "high"

    repeated_weak_topic = any(
        topic.get("submission_count", 0) >= 2 for topic in weak_topics
    )
    if average_percentage < LOW_SCORE_THRESHOLD or repeated_weak_topic:
        return "medium"

    return "low"


def generate_recommendation(
    *,
    risk_level,
    average_percentage,
    missed_assignment_count,
    weak_topics,
):
    if missed_assignment_count >= 3:
        return "Follow up urgently on missed assignments and contact the learner's guardian if the pattern continues."

    if risk_level == "high":
        return "Schedule one-on-one remediation and give a short recovery assignment on the weakest topic."

    if weak_topics:
        topic_names = ", ".join(topic["topic"] for topic in weak_topics[:2])
        return f"Reteach or review {topic_names}, then assign targeted practice."

    if average_percentage < LOW_SCORE_THRESHOLD:
        return "Review recent mistakes with the student and assign lower-stakes practice."

    return "Monitor performance and continue regular practice."


def get_admin_overview(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    students = get_school_students(school)
    teachers = get_school_teachers(school)
    class_arms = get_school_class_arms(school)
    subjects = get_school_subjects(school)
    assignments = get_school_assignments(school)
    submissions = get_school_submissions(school)
    graded_submissions = submissions.filter(graded_at__isnull=False)

    weak_students = get_admin_weak_students(user, school_id=school_id)
    weak_classes = [
        item
        for item in get_admin_class_performance(user, school_id=school_id)
        if item["risk_level"] != "low"
    ]
    weak_subjects = [
        item
        for item in get_admin_subject_performance(user, school_id=school_id)
        if item["risk_level"] != "low"
    ]

    recent_assignments = [
        {
            "id": assignment.id,
            "title": assignment.title,
            "teacher_name": assignment.teacher.full_name,
            "class_arm": str(assignment.class_arm),
            "subject": assignment.subject.name,
            "topic": assignment.topic.title,
            "status": assignment.status,
            "due_at": assignment.due_at,
            "created_at": assignment.created_at,
        }
        for assignment in assignments.order_by("-created_at")[:8]
    ]

    recent_low_performing_students = []
    seen_students = set()
    low_submissions = (
        graded_submissions.filter(percentage__lt=LOW_SCORE_THRESHOLD)
        .select_related(
            "student",
            "student__student_profile",
            "assignment",
            "assignment__subject",
            "assignment__topic",
            "assignment__class_arm",
        )
        .order_by("-graded_at")
    )
    for submission in low_submissions:
        if submission.student_id in seen_students:
            continue
        seen_students.add(submission.student_id)
        recent_low_performing_students.append(
            {
                "student_id": submission.student_id,
                "student_name": submission.student.full_name,
                "admission_number": admission_number_for(submission.student),
                "class_arm": str(submission.assignment.class_arm),
                "assignment_id": submission.assignment_id,
                "assignment_title": submission.assignment.title,
                "percentage": percentage_value(submission.percentage),
                "graded_at": submission.graded_at,
            }
        )
        if len(recent_low_performing_students) == 8:
            break

    average_percentage = graded_submissions.aggregate(average=Avg("percentage"))[
        "average"
    ]

    return {
        "total_students": students.count(),
        "total_teachers": teachers.count(),
        "total_class_arms": class_arms.count(),
        "total_subjects": subjects.count(),
        "total_assignments": assignments.count(),
        "published_assignments": assignments.filter(
            status=AssignmentStatus.PUBLISHED,
        ).count(),
        "draft_assignments": assignments.filter(status=AssignmentStatus.DRAFT).count(),
        "closed_assignments": assignments.filter(status=AssignmentStatus.CLOSED).count(),
        "total_submissions": submissions.count(),
        "graded_submissions": graded_submissions.count(),
        "pending_or_not_started_submissions": get_pending_or_not_started_count(
            assignments,
        ),
        "average_school_percentage": percentage_value(average_percentage),
        "weak_students_count": len(weak_students),
        "weak_classes_count": len(weak_classes),
        "weak_subjects_count": len(weak_subjects),
        "recent_assignments": recent_assignments,
        "recent_low_performing_students": recent_low_performing_students,
    }


def get_admin_class_performance(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    class_arms = get_school_class_arms(school)
    assignments = get_school_assignments(school)
    results = []

    for class_arm in class_arms:
        class_assignments = assignments.filter(class_arm=class_arm)
        class_submissions = Submission.objects.filter(
            assignment__in=class_assignments,
        )
        graded_submissions = class_submissions.filter(graded_at__isnull=False)
        average_percentage = percentage_value(
            graded_submissions.aggregate(average=Avg("percentage"))["average"]
        )
        expected_total, submitted_total = get_expected_and_submitted_totals(
            class_assignments,
        )
        submission_rate = calculate_rate(submitted_total, expected_total)
        weak_student_count = get_weak_student_count_for_class(class_arm, class_assignments)
        risk_level = calculate_class_risk_level(
            average_percentage=average_percentage,
            submission_rate=submission_rate,
        )

        results.append(
            {
                "class_arm_id": class_arm.id,
                "class_level": class_arm.class_level.name,
                "class_arm_name": str(class_arm),
                "total_students": StudentEnrollment.objects.filter(
                    school=class_arm.school,
                    class_arm=class_arm,
                    is_active=True,
                )
                .values("student_id")
                .distinct()
                .count(),
                "total_assignments": class_assignments.count(),
                "total_submissions": class_submissions.count(),
                "average_percentage": average_percentage,
                "submission_rate": submission_rate,
                "weak_student_count": weak_student_count,
                "risk_level": risk_level,
                "recommendation": get_class_recommendation(
                    risk_level=risk_level,
                    average_percentage=average_percentage,
                    submission_rate=submission_rate,
                ),
            }
        )

    return sorted(
        results,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["risk_level"]],
            item["average_percentage"],
        ),
    )


def get_admin_subject_performance(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    assignments = get_school_assignments(school)
    subjects = get_school_subjects(school)
    results = []

    for subject in subjects:
        subject_assignments = assignments.filter(subject=subject)
        subject_submissions = Submission.objects.filter(
            assignment__in=subject_assignments,
        )
        graded_submissions = subject_submissions.filter(graded_at__isnull=False)
        average_percentage = percentage_value(
            graded_submissions.aggregate(average=Avg("percentage"))["average"]
        )
        weakest_topics = get_weakest_topics_for_subject(subject_assignments)
        risk_level = calculate_subject_risk_level(
            average_percentage=average_percentage,
            has_submissions=graded_submissions.exists(),
        )

        results.append(
            {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "total_assignments": subject_assignments.count(),
                "total_submissions": subject_submissions.count(),
                "average_percentage": average_percentage,
                "weak_topic_count": len(weakest_topics),
                "weakest_topics": weakest_topics,
                "risk_level": risk_level,
                "recommendation": get_subject_recommendation(
                    risk_level=risk_level,
                    weak_topic_count=len(weakest_topics),
                ),
            }
        )

    return sorted(
        results,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["risk_level"]],
            item["average_percentage"],
        ),
    )


def get_admin_teacher_activity(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    teachers = get_school_teachers(school)
    assignments = get_school_assignments(school)
    results = []

    for teacher in teachers:
        teacher_assignments = assignments.filter(teacher=teacher)
        published_assignments = teacher_assignments.filter(
            status=AssignmentStatus.PUBLISHED,
        )
        graded_submissions = Submission.objects.filter(
            assignment__in=teacher_assignments,
            graded_at__isnull=False,
        )
        average_class_performance = percentage_value(
            graded_submissions.aggregate(average=Avg("percentage"))["average"]
        )
        assigned_scope = TeacherClassSubjectAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        )
        if school is not None:
            assigned_scope = assigned_scope.filter(school=school)
        activity_status = calculate_teacher_activity_status(
            assignments_created=teacher_assignments.count(),
            published_assignments=published_assignments.count(),
        )
        last_assignment = teacher_assignments.order_by("-created_at").first()

        results.append(
            {
                "teacher_id": teacher.id,
                "teacher_name": teacher.full_name,
                "staff_id": getattr(getattr(teacher, "teacher_profile", None), "staff_id", None),
                "assigned_classes_count": assigned_scope.values("class_arm_id")
                .distinct()
                .count(),
                "assigned_subjects_count": assigned_scope.values("subject_id")
                .distinct()
                .count(),
                "assignments_created": teacher_assignments.count(),
                "published_assignments": published_assignments.count(),
                "total_student_submissions": Submission.objects.filter(
                    assignment__in=teacher_assignments,
                ).count(),
                "average_class_performance": average_class_performance,
                "last_assignment_date": (
                    last_assignment.created_at if last_assignment else None
                ),
                "activity_status": activity_status,
                "recommendation": get_teacher_activity_recommendation(activity_status),
            }
        )

    return sorted(
        results,
        key=lambda item: (
            {"inactive": 0, "low_activity": 1, "active": 2}[item["activity_status"]],
            item["teacher_name"],
        ),
    )


def get_admin_weak_students(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    students = get_school_students(school)
    assignments = get_school_assignments(school)
    weak_students = []

    for student in students:
        submissions = list(
            Submission.objects.filter(
                assignment__in=assignments,
                student=student,
            ).select_related(
                "assignment",
                "assignment__subject",
                "assignment__topic",
                "assignment__class_arm",
            )
        )
        graded_submissions = [
            submission for submission in submissions if submission.graded_at is not None
        ]
        percentages = [float(submission.percentage) for submission in graded_submissions]
        average_percentage = (
            round(sum(percentages) / len(percentages), 2) if percentages else 0.0
        )
        below_40_count = sum(1 for value in percentages if value < LOW_SCORE_THRESHOLD)
        missed_assignments = get_missed_assignments(assignments, student, submissions)
        weak_topics = get_student_weak_topics_from_submissions(graded_submissions)
        weak_subjects = get_student_weak_subjects_from_submissions(graded_submissions)

        is_weak = (
            (graded_submissions and average_percentage < LOW_SCORE_THRESHOLD)
            or below_40_count >= 2
            or len(missed_assignments) >= 2
        )
        if not is_weak:
            continue

        risk_level = calculate_risk_level(
            average_percentage=average_percentage,
            missed_assignment_count=len(missed_assignments),
            weak_topics=weak_topics,
        )
        weak_students.append(
            {
                "student_id": student.id,
                "student_name": student.full_name,
                "admission_number": admission_number_for(student),
                "class_arm": class_arm_name_for_student(student),
                "average_percentage": average_percentage,
                "graded_submission_count": len(graded_submissions),
                "missed_assignment_count": len(missed_assignments),
                "weak_subjects": weak_subjects,
                "weak_topics": weak_topics,
                "risk_level": risk_level,
                "recommendation": generate_recommendation(
                    risk_level=risk_level,
                    average_percentage=average_percentage,
                    missed_assignment_count=len(missed_assignments),
                    weak_topics=weak_topics,
                ),
            }
        )

    return sorted(
        weak_students,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["risk_level"]],
            item["average_percentage"],
            -item["missed_assignment_count"],
        ),
    )


def get_admin_assignment_compliance(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    assignments = get_school_assignments(school)
    compliance_rows = []

    for assignment in assignments.order_by("-created_at"):
        expected_students = get_assignment_expected_students(assignment).count()
        submissions = get_assignment_submissions(assignment)
        started_count = submissions.filter(started_at__isnull=False).count()
        submitted_count = submissions.filter(
            Q(submitted_at__isnull=False)
            | Q(status__in=[
                SubmissionStatus.SUBMITTED,
                SubmissionStatus.GRADED,
                SubmissionStatus.AUTO_SUBMITTED,
            ])
        ).count()
        graded_count = submissions.filter(graded_at__isnull=False).count()
        submission_rate = calculate_rate(submitted_count, expected_students)
        compliance_status = calculate_compliance_status(submission_rate)

        compliance_rows.append(
            {
                "assignment_id": assignment.id,
                "title": assignment.title,
                "teacher_name": assignment.teacher.full_name,
                "class_arm": str(assignment.class_arm),
                "subject": assignment.subject.name,
                "topic": assignment.topic.title,
                "status": assignment.status,
                "due_at": assignment.due_at,
                "expected_students": expected_students,
                "started_count": started_count,
                "submitted_count": submitted_count,
                "graded_count": graded_count,
                "not_started_count": max(expected_students - started_count, 0),
                "submission_rate": submission_rate,
                "compliance_status": compliance_status,
            }
        )

    return sorted(
        compliance_rows,
        key=lambda item: (
            {"poor": 0, "warning": 1, "good": 2}[item["compliance_status"]],
            item["due_at"] is None,
            item["due_at"],
        ),
    )


def normalize_admin_intervention_risk(value):
    if value in {"critical", "high", "moderate", "low"}:
        return value
    if value in {"poor", "inactive"}:
        return "high"
    if value in {"medium", "warning", "low_activity"}:
        return "moderate"
    if value in {"good", "active"}:
        return "low"
    return "low"


def intervention_risk_from_average(average_score, *, has_evidence=True):
    if not has_evidence:
        return "low"
    if average_score < 30:
        return "critical"
    if average_score < 40:
        return "high"
    if average_score < 50:
        return "moderate"
    return "low"


def highest_intervention_risk(*levels):
    return max(
        (level for level in levels if level),
        key=lambda level: RISK_LEVEL_WEIGHT.get(level, 0),
        default="low",
    )


def action_payload(label, href, **params):
    return {
        "label": label,
        "href": href,
        "params": {
            key: value
            for key, value in params.items()
            if value is not None and value != ""
        },
    }


def risk_sort_key(item):
    return (
        -RISK_LEVEL_WEIGHT.get(item.get("risk_level", "low"), 0),
        item.get("average_score", 100),
        -item.get("weak_student_count", 0),
        item.get("title", ""),
    )


def score_from_risks(items):
    points = 0
    for item in items:
        risk = item.get("risk_level", "low")
        if risk == "critical":
            points += 25
        elif risk == "high":
            points += 15
        elif risk == "moderate":
            points += 7
    return min(points, 100)


def overall_intervention_risk_level(risk_score):
    if risk_score >= 70:
        return "critical"
    if risk_score >= 40:
        return "high"
    if risk_score >= 15:
        return "moderate"
    return "low"


def top_weak_subjects_for_class(weak_students, class_arm_name):
    grouped = {}
    for student in weak_students:
        if student.get("class_arm") != class_arm_name:
            continue
        for subject in student.get("weak_subjects", []):
            item = grouped.setdefault(
                subject["subject"],
                {
                    "subject": subject["subject"],
                    "scores": [],
                    "student_ids": set(),
                },
            )
            item["scores"].append(float(subject["average_percentage"]))
            item["student_ids"].add(student["student_id"])

    return [
        {
            "subject": item["subject"],
            "average_percentage": round(sum(item["scores"]) / len(item["scores"]), 2),
            "weak_student_count": len(item["student_ids"]),
        }
        for item in sorted(
            grouped.values(),
            key=lambda value: (
                sum(value["scores"]) / len(value["scores"]),
                -len(value["student_ids"]),
            ),
        )[:3]
    ]


def top_weak_topics_for_class(weak_students, class_arm_name):
    grouped = {}
    for student in weak_students:
        if student.get("class_arm") != class_arm_name:
            continue
        for topic in student.get("weak_topics", []):
            key = (topic.get("subject"), topic.get("topic"))
            item = grouped.setdefault(
                key,
                {
                    "subject": topic.get("subject"),
                    "topic": topic.get("topic"),
                    "scores": [],
                    "student_ids": set(),
                },
            )
            item["scores"].append(float(topic["average_percentage"]))
            item["student_ids"].add(student["student_id"])

    return [
        {
            "subject": item["subject"],
            "topic": item["topic"],
            "average_percentage": round(sum(item["scores"]) / len(item["scores"]), 2),
            "weak_student_count": len(item["student_ids"]),
        }
        for item in sorted(
            grouped.values(),
            key=lambda value: (
                sum(value["scores"]) / len(value["scores"]),
                -len(value["student_ids"]),
            ),
        )[:3]
    ]


def build_class_interventions(class_rows, weak_students):
    interventions = []
    for row in class_rows:
        if (
            row["total_assignments"] == 0
            and row["total_submissions"] == 0
            and row["weak_student_count"] == 0
        ):
            continue

        base_risk = normalize_admin_intervention_risk(row["risk_level"])
        evidence_risk = intervention_risk_from_average(
            row["average_percentage"],
            has_evidence=row["total_submissions"] > 0,
        )
        risk_level = highest_intervention_risk(base_risk, evidence_risk)
        if risk_level == "low" and row["weak_student_count"] == 0:
            continue

        class_arm_name = row["class_arm_name"]
        interventions.append(
            {
                "class_arm_id": row["class_arm_id"],
                "class_arm_name": class_arm_name,
                "class_level": row["class_level"],
                "average_score": row["average_percentage"],
                "submitted_count": row["total_submissions"],
                "weak_student_count": row["weak_student_count"],
                "risk_level": risk_level,
                "main_weak_subjects": top_weak_subjects_for_class(
                    weak_students,
                    class_arm_name,
                ),
                "main_weak_topics": top_weak_topics_for_class(
                    weak_students,
                    class_arm_name,
                ),
                "recommended_action": row["recommendation"],
                "action_payload": action_payload(
                    "View Class Analytics",
                    "/admin/analytics/classes",
                    class_arm=row["class_arm_id"],
                ),
            }
        )

    return sorted(interventions, key=risk_sort_key)[:ADMIN_INTERVENTION_LIMIT]


def build_subject_interventions(subject_rows, weak_students):
    interventions = []
    for row in subject_rows:
        weak_student_ids = set()
        affected_class_arms = set()
        for student in weak_students:
            for subject in student.get("weak_subjects", []):
                if subject.get("subject") != row["subject_name"]:
                    continue
                weak_student_ids.add(student["student_id"])
                if student.get("class_arm"):
                    affected_class_arms.add(student["class_arm"])

        risk_level = highest_intervention_risk(
            normalize_admin_intervention_risk(row["risk_level"]),
            intervention_risk_from_average(
                row["average_percentage"],
                has_evidence=row["total_submissions"] > 0,
            ),
        )
        if (
            risk_level == "low"
            and row["weak_topic_count"] == 0
            and not weak_student_ids
        ):
            continue

        interventions.append(
            {
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"],
                "average_score": row["average_percentage"],
                "weak_class_count": len(affected_class_arms),
                "weak_student_count": len(weak_student_ids),
                "affected_class_arms": sorted(affected_class_arms),
                "risk_level": risk_level,
                "weakest_topics": row["weakest_topics"],
                "recommended_action": row["recommendation"],
                "action_payload": action_payload(
                    "View Subject Analytics",
                    "/admin/analytics/subjects",
                    subject=row["subject_id"],
                ),
            }
        )

    return sorted(interventions, key=risk_sort_key)[:ADMIN_INTERVENTION_LIMIT]


def teacher_email_map_for_school(school):
    return {
        teacher.id: teacher.email
        for teacher in get_school_teachers(school)
    }


def teacher_scope_map_for_school(school):
    scope = TeacherClassSubjectAssignment.objects.select_related(
        "class_arm",
        "class_arm__class_level",
        "subject",
    ).filter(is_active=True)
    if school is not None:
        scope = scope.filter(school=school)

    mapped = defaultdict(list)
    for assignment in scope:
        mapped[assignment.teacher_id].append(
            {
                "class_arm_id": assignment.class_arm_id,
                "class_arm_name": str(assignment.class_arm),
                "subject_id": assignment.subject_id,
                "subject_name": assignment.subject.name,
            }
        )
    return mapped


def build_teacher_interventions(teacher_rows, school):
    emails = teacher_email_map_for_school(school)
    scopes = teacher_scope_map_for_school(school)
    school_assignments = get_school_assignments(school)
    interventions = []

    for row in teacher_rows:
        teacher_assignments = school_assignments.filter(teacher_id=row["teacher_id"])
        expected_total, submitted_total = get_expected_and_submitted_totals(
            teacher_assignments,
        )
        submission_rate = calculate_rate(submitted_total, expected_total)
        performance_risk = intervention_risk_from_average(
            row["average_class_performance"],
            has_evidence=row["total_student_submissions"] > 0,
        )
        compliance_risk = (
            "high"
            if expected_total and submission_rate < 50
            else "moderate"
            if expected_total and submission_rate < 70
            else "low"
        )
        activity_risk = normalize_admin_intervention_risk(row["activity_status"])
        risk_level = highest_intervention_risk(
            activity_risk,
            performance_risk,
            compliance_risk,
        )
        if risk_level == "low":
            continue

        interventions.append(
            {
                "teacher_id": row["teacher_id"],
                "teacher_name": row["teacher_name"],
                "teacher_email": emails.get(row["teacher_id"], ""),
                "staff_id": row["staff_id"],
                "classes_subjects_taught": scopes.get(row["teacher_id"], []),
                "assignment_count": row["assignments_created"],
                "published_assignment_count": row["published_assignments"],
                "average_class_score": row["average_class_performance"],
                "submission_rate": submission_rate,
                "submitted_count": submitted_total,
                "expected_submission_count": expected_total,
                "risk_level": risk_level,
                "recommended_action": row["recommendation"],
                "action_payload": action_payload(
                    "View Teacher Activity",
                    "/admin/analytics/teachers",
                    teacher=row["teacher_id"],
                ),
            }
        )

    return sorted(interventions, key=risk_sort_key)[:ADMIN_INTERVENTION_LIMIT]


def build_weak_student_clusters(weak_students):
    grouped = {}
    for student in weak_students:
        for topic in student.get("weak_topics", []):
            key = (
                student.get("class_arm") or "Class not set",
                topic.get("subject") or "Subject not set",
                topic.get("topic") or "Topic not set",
            )
            item = grouped.setdefault(
                key,
                {
                    "class_arm": key[0],
                    "subject": key[1],
                    "topic": key[2],
                    "scores": [],
                    "student_ids": set(),
                },
            )
            item["scores"].append(float(topic["average_percentage"]))
            item["student_ids"].add(student["student_id"])

    clusters = []
    for item in grouped.values():
        average_score = round(sum(item["scores"]) / len(item["scores"]), 2)
        weak_student_count = len(item["student_ids"])
        risk_level = highest_intervention_risk(
            intervention_risk_from_average(average_score),
            "high" if weak_student_count >= 3 else "moderate",
        )
        clusters.append(
            {
                "class_arm": item["class_arm"],
                "subject": item["subject"],
                "topic": item["topic"],
                "weak_student_count": weak_student_count,
                "average_score": average_score,
                "risk_level": risk_level,
                "recommended_action": (
                    "Ask the class teacher to reteach this topic and assign targeted "
                    "follow-up questions."
                ),
                "action_payload": action_payload(
                    "View Weak Students",
                    "/admin/analytics/weak-students",
                    class_arm=item["class_arm"],
                    subject=item["subject"],
                    topic=item["topic"],
                ),
            }
        )

    return sorted(clusters, key=risk_sort_key)[:ADMIN_INTERVENTION_LIMIT]


def build_compliance_alerts(compliance_rows):
    alerts = []
    for row in compliance_rows:
        if row["compliance_status"] == "good" and row["not_started_count"] == 0:
            continue

        risk_level = normalize_admin_intervention_risk(row["compliance_status"])
        if row["submission_rate"] < 40 and row["expected_students"]:
            risk_level = "critical"
        elif row["submission_rate"] < 50 and row["expected_students"]:
            risk_level = "high"

        alerts.append(
            {
                "assignment_id": row["assignment_id"],
                "title": row["title"],
                "teacher_name": row["teacher_name"],
                "class_arm": row["class_arm"],
                "subject": row["subject"],
                "topic": row["topic"],
                "expected_students": row["expected_students"],
                "started_count": row["started_count"],
                "submitted_count": row["submitted_count"],
                "not_started_count": row["not_started_count"],
                "submission_rate": row["submission_rate"],
                "risk_level": risk_level,
                "recommended_action": (
                    "Follow up on students who have not started and ask the teacher "
                    "to send a reminder."
                ),
                "action_payload": action_payload(
                    "View Compliance",
                    "/admin/analytics/compliance",
                    assignment=row["assignment_id"],
                ),
            }
        )

    return sorted(alerts, key=risk_sort_key)[:ADMIN_INTERVENTION_LIMIT]


def build_urgent_interventions(
    class_interventions,
    subject_interventions,
    teacher_interventions,
    weak_student_clusters,
    compliance_alerts,
):
    urgent = []
    for item in class_interventions:
        urgent.append(
            {
                "category": "class",
                "title": item["class_arm_name"],
                "description": (
                    f"{item['class_arm_name']} averages {item['average_score']}% "
                    f"with {item['weak_student_count']} weak students."
                ),
                "risk_level": item["risk_level"],
                "recommended_action": item["recommended_action"],
                "action_payload": item["action_payload"],
            }
        )
    for item in subject_interventions:
        urgent.append(
            {
                "category": "subject",
                "title": item["subject_name"],
                "description": (
                    f"{item['subject_name']} averages {item['average_score']}% "
                    f"with {item['weak_student_count']} weak students."
                ),
                "risk_level": item["risk_level"],
                "recommended_action": item["recommended_action"],
                "action_payload": item["action_payload"],
            }
        )
    for item in teacher_interventions:
        urgent.append(
            {
                "category": "teacher",
                "title": item["teacher_name"],
                "description": (
                    f"{item['teacher_name']} has {item['assignment_count']} "
                    "assignments and needs follow-up."
                ),
                "risk_level": item["risk_level"],
                "recommended_action": item["recommended_action"],
                "action_payload": item["action_payload"],
            }
        )
    for item in weak_student_clusters:
        urgent.append(
            {
                "category": "weak_student_cluster",
                "title": f"{item['topic']} - {item['class_arm']}",
                "description": (
                    f"{item['weak_student_count']} students are weak in "
                    f"{item['topic']}."
                ),
                "risk_level": item["risk_level"],
                "recommended_action": item["recommended_action"],
                "action_payload": item["action_payload"],
            }
        )
    for item in compliance_alerts:
        urgent.append(
            {
                "category": "assignment_compliance",
                "title": item["title"],
                "description": (
                    f"{item['not_started_count']} of {item['expected_students']} "
                    "students have not started."
                ),
                "risk_level": item["risk_level"],
                "recommended_action": item["recommended_action"],
                "action_payload": item["action_payload"],
            }
        )

    return [
        item
        for item in sorted(urgent, key=risk_sort_key)
        if item["risk_level"] != "low"
    ][:ADMIN_INTERVENTION_LIMIT]


def empty_admin_intervention_dashboard(overview):
    return {
        "summary": {
            "total_classes_at_risk": 0,
            "total_subjects_at_risk": 0,
            "total_teachers_at_risk": 0,
            "total_weak_student_clusters": 0,
            "total_compliance_alerts": 0,
            "total_urgent_interventions": 0,
            "average_school_percentage": overview["average_school_percentage"],
            "overall_risk_level": "low",
            "message": "Publish assignments and collect submissions to unlock intervention insights.",
        },
        "risk_score": 0,
        "overall_risk_level": "low",
        "urgent_interventions": [],
        "class_interventions": [],
        "subject_interventions": [],
        "teacher_interventions": [],
        "weak_student_clusters": [],
        "assignment_compliance_alerts": [],
        "recommended_actions": [],
    }


def get_admin_intervention_dashboard(user, school_id=None):
    school = get_school_for_admin(user, school_id)
    overview = get_admin_overview(user, school_id=school_id)
    if overview["total_assignments"] == 0:
        return empty_admin_intervention_dashboard(overview)

    class_rows = get_admin_class_performance(user, school_id=school_id)
    subject_rows = get_admin_subject_performance(user, school_id=school_id)
    teacher_rows = get_admin_teacher_activity(user, school_id=school_id)
    weak_students = get_admin_weak_students(user, school_id=school_id)
    compliance_rows = get_admin_assignment_compliance(user, school_id=school_id)

    class_interventions = build_class_interventions(class_rows, weak_students)
    subject_interventions = build_subject_interventions(subject_rows, weak_students)
    teacher_interventions = build_teacher_interventions(teacher_rows, school)
    weak_student_clusters = build_weak_student_clusters(weak_students)
    assignment_compliance_alerts = build_compliance_alerts(compliance_rows)
    urgent_interventions = build_urgent_interventions(
        class_interventions,
        subject_interventions,
        teacher_interventions,
        weak_student_clusters,
        assignment_compliance_alerts,
    )
    risk_score = score_from_risks(urgent_interventions)
    overall_risk_level = overall_intervention_risk_level(risk_score)

    summary = {
        "total_classes_at_risk": len(class_interventions),
        "total_subjects_at_risk": len(subject_interventions),
        "total_teachers_at_risk": len(teacher_interventions),
        "total_weak_student_clusters": len(weak_student_clusters),
        "total_compliance_alerts": len(assignment_compliance_alerts),
        "total_urgent_interventions": len(urgent_interventions),
        "average_school_percentage": overview["average_school_percentage"],
        "overall_risk_level": overall_risk_level,
        "message": (
            "Urgent support areas found. Start with the highest-risk classes, "
            "subjects, and weak student clusters."
            if urgent_interventions
            else "No urgent academic interventions are currently detected."
        ),
    }

    return {
        "summary": summary,
        "risk_score": risk_score,
        "overall_risk_level": overall_risk_level,
        "urgent_interventions": urgent_interventions,
        "class_interventions": class_interventions,
        "subject_interventions": subject_interventions,
        "teacher_interventions": teacher_interventions,
        "weak_student_clusters": weak_student_clusters,
        "assignment_compliance_alerts": assignment_compliance_alerts,
        "recommended_actions": urgent_interventions[:5],
    }


def teacher_can_view_student_progress(teacher, student):
    if not teacher or teacher.role != UserRole.TEACHER or not teacher.school_id:
        return False
    if student.school_id != teacher.school_id:
        return False

    teaches_student_class = TeacherClassSubjectAssignment.objects.filter(
        school=teacher.school,
        teacher=teacher,
        is_active=True,
        class_arm_id__in=StudentEnrollment.objects.filter(
            school=teacher.school,
            student=student,
            is_active=True,
        ).values("class_arm_id"),
    ).exists()
    if teaches_student_class:
        return True

    return Submission.objects.filter(
        school=teacher.school,
        student=student,
        assignment__teacher=teacher,
    ).exists()


def resolve_student_for_progress_report(user, student_id, school_id=None):
    student_queryset = get_school_students(None).select_related("school")

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
        return get_object_or_404(
            student_queryset.filter(school=user.school),
            pk=student_id,
        )

    if user.role == UserRole.PLATFORM_ADMIN or getattr(user, "is_superuser", False):
        if school_id:
            student_queryset = student_queryset.filter(school_id=school_id)
        return get_object_or_404(student_queryset, pk=student_id)

    if user.role == UserRole.TEACHER:
        student = get_object_or_404(
            student_queryset.filter(school=user.school),
            pk=student_id,
        )
        if teacher_can_view_student_progress(user, student):
            return student
        raise PermissionDenied("You do not teach this student.")

    raise PermissionDenied("You do not have access to student progress reports.")


def _active_student_enrollment(student):
    if not student.school_id:
        return None
    return (
        StudentEnrollment.objects.filter(
            school=student.school,
            student=student,
            is_active=True,
        )
        .select_related("class_arm", "class_arm__class_level", "academic_session", "term")
        .order_by("-created_at")
        .first()
    )


def _student_profile_for_report(student):
    enrollment = _active_student_enrollment(student)
    class_arm = enrollment.class_arm if enrollment else None
    return {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email,
        "admission_number": admission_number_for(student),
        "class_arm": str(class_arm) if class_arm else None,
        "class_arm_id": class_arm.id if class_arm else None,
        "class_level": class_arm.class_level.name if class_arm else None,
        "class_level_id": class_arm.class_level_id if class_arm else None,
        "school": student.school.name if student.school_id else None,
        "school_id": student.school_id,
    }


def _weighted_average_from_scores(score, total_marks):
    if not total_marks:
        return None
    return round(score / total_marks * 100, 2)


def _report_average(value):
    return 0.0 if value is None else percentage_value(value)


def _assignment_queryset_for_progress(user, student):
    if user.role == UserRole.TEACHER:
        return get_teacher_assignments(user)
    return get_school_assignments(student.school)


def _graded_assignment_submissions_for_progress(assignments, student):
    return list(
        Submission.objects.filter(
            assignment__in=assignments,
            student=student,
            graded_at__isnull=False,
        )
        .select_related(
            "assignment",
            "assignment__subject",
            "assignment__topic",
            "assignment__class_arm",
            "assignment__teacher",
        )
        .order_by("-graded_at", "-updated_at")
    )


def _assignment_breakdown(graded_submissions, group_type):
    grouped = {}
    for submission in graded_submissions:
        assignment = submission.assignment
        if group_type == "subject":
            key = assignment.subject_id
            defaults = {
                "subject_id": assignment.subject_id,
                "subject_name": assignment.subject.name,
            }
        else:
            key = assignment.topic_id
            defaults = {
                "subject_id": assignment.subject_id,
                "subject_name": assignment.subject.name,
                "topic_id": assignment.topic_id,
                "topic_title": assignment.topic.title,
            }

        item = grouped.setdefault(
            key,
            {
                **defaults,
                "graded_assignments_count": 0,
                "score": 0,
                "total_marks": 0,
                "last_graded_at": None,
            },
        )
        item["graded_assignments_count"] += 1
        item["score"] += submission.score
        item["total_marks"] += submission.total_marks
        if (
            item["last_graded_at"] is None
            or (
                submission.graded_at is not None
                and submission.graded_at > item["last_graded_at"]
            )
        ):
            item["last_graded_at"] = submission.graded_at

    rows = []
    for item in grouped.values():
        score = item.pop("score")
        total_marks = item.pop("total_marks")
        item["average_percentage"] = _report_average(
            _weighted_average_from_scores(score, total_marks)
        )
        rows.append(item)

    return sorted(rows, key=lambda row: row["average_percentage"])


def _recent_assignment_results(graded_submissions, limit=10):
    return [
        {
            "submission_id": submission.id,
            "assignment_id": submission.assignment_id,
            "assignment_title": submission.assignment.title,
            "teacher_name": submission.assignment.teacher.full_name,
            "class_arm": str(submission.assignment.class_arm),
            "subject_id": submission.assignment.subject_id,
            "subject_name": submission.assignment.subject.name,
            "topic_id": submission.assignment.topic_id,
            "topic_title": submission.assignment.topic.title,
            "score": submission.score,
            "total_marks": submission.total_marks,
            "percentage": percentage_value(submission.percentage),
            "submitted_at": submission.submitted_at,
            "graded_at": submission.graded_at,
        }
        for submission in graded_submissions[:limit]
    ]


def _practice_sessions_for_progress(student):
    if not student.school_id:
        return PracticeSession.objects.none()

    return PracticeSession.objects.filter(
        school=student.school,
        student=student,
        status=PracticeSessionStatus.SUBMITTED,
    ).select_related("subject", "topic", "class_level", "class_arm")


def _practice_breakdown(sessions, group_type):
    grouped = {}
    for session in sessions:
        if group_type == "topic" and not session.topic_id:
            continue
        if group_type == "subject":
            key = session.subject_id
            defaults = {
                "subject_id": session.subject_id,
                "subject_name": session.subject.name,
            }
        else:
            key = session.topic_id
            defaults = {
                "subject_id": session.subject_id,
                "subject_name": session.subject.name,
                "topic_id": session.topic_id,
                "topic_title": session.topic.title,
            }

        item = grouped.setdefault(
            key,
            {
                **defaults,
                "sessions_completed": 0,
                "questions_answered": 0,
                "correct_answers": 0,
                "score": 0,
                "total_marks": 0,
                "last_practiced_at": None,
            },
        )
        item["sessions_completed"] += 1
        item["questions_answered"] += session.answers.count()
        item["correct_answers"] += session.answers.filter(is_correct=True).count()
        item["score"] += session.score
        item["total_marks"] += session.total_marks
        if (
            item["last_practiced_at"] is None
            or (
                session.submitted_at is not None
                and session.submitted_at > item["last_practiced_at"]
            )
        ):
            item["last_practiced_at"] = session.submitted_at

    rows = []
    for item in grouped.values():
        score = item.pop("score")
        total_marks = item.pop("total_marks")
        item["average_percentage"] = _report_average(
            _weighted_average_from_scores(score, total_marks)
        )
        rows.append(item)

    return sorted(rows, key=lambda row: row["average_percentage"])


def _recent_practice_sessions(sessions, limit=10):
    return [
        {
            "id": session.id,
            "subject_id": session.subject_id,
            "subject_name": session.subject.name,
            "topic_id": session.topic_id,
            "topic_title": session.topic.title if session.topic_id else None,
            "class_level_id": session.class_level_id,
            "class_level_name": session.class_level.name if session.class_level_id else None,
            "difficulty": session.difficulty,
            "question_count_requested": session.question_count_requested,
            "score": session.score,
            "total_marks": session.total_marks,
            "percentage": percentage_value(session.percentage),
            "submitted_at": session.submitted_at,
        }
        for session in sorted(
            sessions,
            key=lambda session: session.submitted_at or session.updated_at,
            reverse=True,
        )[:limit]
    ]


def _combined_topic_rows(assignment_topic_rows, practice_topic_rows):
    grouped = {}
    for row in assignment_topic_rows:
        item = grouped.setdefault(
            row["topic_id"],
            {
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"],
                "topic_id": row["topic_id"],
                "topic_title": row["topic_title"],
                "assignment_average": None,
                "practice_average": None,
                "assignment_count": 0,
                "practice_sessions_count": 0,
            },
        )
        item["assignment_average"] = row["average_percentage"]
        item["assignment_count"] = row["graded_assignments_count"]

    for row in practice_topic_rows:
        item = grouped.setdefault(
            row["topic_id"],
            {
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"],
                "topic_id": row["topic_id"],
                "topic_title": row["topic_title"],
                "assignment_average": None,
                "practice_average": None,
                "assignment_count": 0,
                "practice_sessions_count": 0,
            },
        )
        item["practice_average"] = row["average_percentage"]
        item["practice_sessions_count"] = row["sessions_completed"]

    rows = []
    for item in grouped.values():
        averages = [
            value
            for value in [item["assignment_average"], item["practice_average"]]
            if value is not None
        ]
        item["average_percentage"] = (
            round(sum(averages) / len(averages), 2) if averages else 0.0
        )
        item["evidence_count"] = (
            item["assignment_count"] + item["practice_sessions_count"]
        )
        rows.append(item)
    return rows


def _progress_weak_topics(assignment_topic_rows, practice_topic_rows, limit=8):
    rows = [
        row
        for row in _combined_topic_rows(assignment_topic_rows, practice_topic_rows)
        if row["average_percentage"] < WEAK_TOPIC_THRESHOLD
    ]
    return sorted(rows, key=lambda row: (row["average_percentage"], -row["evidence_count"]))[
        :limit
    ]


def _progress_strong_topics(assignment_topic_rows, practice_topic_rows, limit=8):
    rows = [
        row
        for row in _combined_topic_rows(assignment_topic_rows, practice_topic_rows)
        if row["average_percentage"] >= 70
    ]
    return sorted(
        rows,
        key=lambda row: (-row["average_percentage"], -row["evidence_count"]),
    )[:limit]


def _student_progress_risk_level(
    overall_average,
    missed_assignments_count,
    *,
    has_performance_evidence,
):
    if not has_performance_evidence and missed_assignments_count == 0:
        return "low"
    if missed_assignments_count >= 3 or overall_average < 40:
        return "critical"
    if overall_average < 50:
        return "high"
    if overall_average < 65:
        return "moderate"
    return "low"


def _progress_recommendations(weak_topics, missed_assignments, profile, limit=5):
    recommendations = []
    for row in weak_topics[:limit]:
        question_count = 5
        title = f"Remedial: {row['topic_title']}"
        instructions = (
            f"Focus on {row['topic_title']} because recent performance is "
            f"{row['average_percentage']:.2f}%."
        )
        query = urlencode(
            {
                "classArm": profile["class_arm_id"] or "",
                "subject": row["subject_id"],
                "topic": row["topic_id"],
                "questionCount": question_count,
                "title": title,
                "instructions": instructions,
                "remedial": "true",
            }
        )
        recommendations.append(
            {
                "recommended_action": "Schedule targeted practice or a remedial assignment.",
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"],
                "topic_id": row["topic_id"],
                "topic_title": row["topic_title"],
                "reason": (
                    f"Combined assignment/practice average is "
                    f"{row['average_percentage']:.2f}%."
                ),
                "action_payload": {
                    "type": "remedial_assignment",
                    "class_arm": profile["class_arm_id"],
                    "subject": row["subject_id"],
                    "topic": row["topic_id"],
                    "question_count": question_count,
                    "title": title,
                    "instructions": instructions,
                    "remedial": True,
                    "href": f"/teacher/assignments/new?{query}"
                    if profile["class_arm_id"]
                    else "",
                },
            }
        )

    if len(recommendations) < limit and missed_assignments:
        recommendations.append(
            {
                "recommended_action": "Follow up on missed assignments.",
                "subject_id": None,
                "subject_name": "",
                "topic_id": None,
                "topic_title": "",
                "reason": f"{len(missed_assignments)} published assignment(s) have not been submitted.",
                "action_payload": {
                    "type": "missed_assignment_follow_up",
                    "href": "/admin/analytics/compliance",
                },
            }
        )

    return recommendations[:limit]


def get_student_progress_report(user, student_id, school_id=None):
    student = resolve_student_for_progress_report(user, student_id, school_id=school_id)
    profile = _student_profile_for_report(student)
    assignments = _assignment_queryset_for_progress(user, student)
    submissions = list(
        Submission.objects.filter(
            assignment__in=assignments,
            student=student,
        ).select_related("assignment", "assignment__subject", "assignment__topic")
    )
    graded_submissions = _graded_assignment_submissions_for_progress(
        assignments,
        student,
    )
    missed_assignments = get_missed_assignments(assignments, student, submissions)
    assignment_subject_breakdown = _assignment_breakdown(
        graded_submissions,
        "subject",
    )
    assignment_topic_breakdown = _assignment_breakdown(graded_submissions, "topic")

    practice_sessions = list(_practice_sessions_for_progress(student))
    practice_subject_breakdown = _practice_breakdown(practice_sessions, "subject")
    practice_topic_breakdown = _practice_breakdown(practice_sessions, "topic")

    assignment_score = sum(submission.score for submission in graded_submissions)
    assignment_total_marks = sum(submission.total_marks for submission in graded_submissions)
    practice_score = sum(session.score for session in practice_sessions)
    practice_total_marks = sum(session.total_marks for session in practice_sessions)
    assignment_average = _weighted_average_from_scores(
        assignment_score,
        assignment_total_marks,
    )
    practice_average = _weighted_average_from_scores(
        practice_score,
        practice_total_marks,
    )
    overall_average = _weighted_average_from_scores(
        assignment_score + practice_score,
        assignment_total_marks + practice_total_marks,
    )
    weak_topics = _progress_weak_topics(
        assignment_topic_breakdown,
        practice_topic_breakdown,
    )
    strong_topics = _progress_strong_topics(
        assignment_topic_breakdown,
        practice_topic_breakdown,
    )
    overall_average_value = _report_average(overall_average)
    risk_level = _student_progress_risk_level(
        overall_average_value,
        len(missed_assignments),
        has_performance_evidence=bool(
            assignment_total_marks + practice_total_marks
        ),
    )

    learning_path = get_student_learning_path(student)

    return {
        "student": profile,
        "summary": {
            "assignment_average": _report_average(assignment_average),
            "practice_average": _report_average(practice_average),
            "overall_average": overall_average_value,
            "graded_assignments_count": len(graded_submissions),
            "missed_assignments_count": len(missed_assignments),
            "practice_sessions_count": len(practice_sessions),
            "weak_topic_count": len(weak_topics),
            "strong_topic_count": len(strong_topics),
            "risk_level": risk_level,
        },
        "assignment_performance": {
            "recent_results": _recent_assignment_results(graded_submissions),
            "subject_breakdown": assignment_subject_breakdown,
            "topic_breakdown": assignment_topic_breakdown,
            "missed_assignments": missed_assignments,
        },
        "practice_performance": {
            "recent_sessions": _recent_practice_sessions(practice_sessions),
            "subject_breakdown": practice_subject_breakdown,
            "topic_breakdown": practice_topic_breakdown,
        },
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "recommendations": _progress_recommendations(
            weak_topics,
            missed_assignments,
            profile,
        ),
        "learning_path_summary": {
            "overall_status": learning_path["overall_status"],
            "headline": learning_path["headline"],
            "message": learning_path["message"],
            "recommended_next_action": learning_path["recommended_next_action"],
        },
        "generated_at": timezone.now(),
    }


def get_pending_or_not_started_count(assignments):
    count = 0
    for assignment in assignments.filter(status=AssignmentStatus.PUBLISHED):
        expected = get_assignment_expected_students(assignment).count()
        graded = assignment.submissions.filter(graded_at__isnull=False).count()
        count += max(expected - graded, 0)
    return count


def get_expected_and_submitted_totals(assignments):
    expected_total = 0
    submitted_total = 0
    for assignment in assignments:
        expected_total += get_assignment_expected_students(assignment).count()
        submitted_total += assignment.submissions.filter(
            Q(submitted_at__isnull=False)
            | Q(status__in=[
                SubmissionStatus.SUBMITTED,
                SubmissionStatus.GRADED,
                SubmissionStatus.AUTO_SUBMITTED,
            ])
        ).count()
    return expected_total, submitted_total


def get_weak_student_count_for_class(class_arm, assignments):
    student_ids = StudentEnrollment.objects.filter(
        school=class_arm.school,
        class_arm=class_arm,
        is_active=True,
    ).values_list("student_id", flat=True)
    weak_count = 0

    for student_id in student_ids:
        submissions = Submission.objects.filter(
            assignment__in=assignments,
            student_id=student_id,
            graded_at__isnull=False,
        )
        average = submissions.aggregate(average=Avg("percentage"))["average"]
        if average is not None and float(average) < WEAK_TOPIC_THRESHOLD:
            weak_count += 1

    return weak_count


def get_weakest_topics_for_subject(assignments):
    grouped = {}
    submissions = Submission.objects.filter(
        assignment__in=assignments,
        graded_at__isnull=False,
    ).select_related("assignment__topic")

    for submission in submissions:
        topic = submission.assignment.topic
        item = grouped.setdefault(topic.id, {"topic": topic.title, "scores": []})
        item["scores"].append(float(submission.percentage))

    weakest_topics = []
    for item in grouped.values():
        average_percentage = round(sum(item["scores"]) / len(item["scores"]), 2)
        if average_percentage < WEAK_TOPIC_THRESHOLD:
            weakest_topics.append(
                {
                    "topic": item["topic"],
                    "average_percentage": average_percentage,
                    "total_submissions": len(item["scores"]),
                }
            )

    return sorted(weakest_topics, key=lambda item: item["average_percentage"])[:5]


def get_student_weak_subjects_from_submissions(graded_submissions):
    grouped = defaultdict(list)
    for submission in graded_submissions:
        grouped[submission.assignment.subject.name].append(float(submission.percentage))

    weak_subjects = []
    for subject, scores in grouped.items():
        average_percentage = round(sum(scores) / len(scores), 2)
        if average_percentage < WEAK_TOPIC_THRESHOLD:
            weak_subjects.append(
                {
                    "subject": subject,
                    "average_percentage": average_percentage,
                    "submission_count": len(scores),
                }
            )
    return sorted(weak_subjects, key=lambda item: item["average_percentage"])


def calculate_rate(numerator, denominator):
    return round(numerator / denominator * 100, 2) if denominator else 0.0


def calculate_class_risk_level(*, average_percentage, submission_rate):
    if average_percentage < 40 or submission_rate < 50:
        return "high"
    if average_percentage < 50 or submission_rate < 60:
        return "medium"
    return "low"


def calculate_subject_risk_level(*, average_percentage, has_submissions):
    if not has_submissions:
        return "low"
    if average_percentage < 40:
        return "high"
    if average_percentage < 50:
        return "medium"
    return "low"


def calculate_teacher_activity_status(*, assignments_created, published_assignments):
    if assignments_created == 0:
        return "inactive"
    if published_assignments < 2:
        return "low_activity"
    return "active"


def calculate_compliance_status(submission_rate):
    if submission_rate >= 80:
        return "good"
    if submission_rate >= 50:
        return "warning"
    return "poor"


def get_class_recommendation(*, risk_level, average_percentage, submission_rate):
    if submission_rate < 60:
        return "Follow up with the class teacher on assignment completion and reminders."
    if average_percentage < 50:
        return "Review weak topics with the class and assign targeted practice."
    if risk_level == "high":
        return "Prioritize this class for academic intervention."
    return "Maintain regular practice and monitor progress."


def get_subject_recommendation(*, risk_level, weak_topic_count):
    if weak_topic_count:
        return "Review the weakest topics and support teachers with focused remediation."
    if risk_level != "low":
        return "Investigate recent assessments and reteach difficult concepts."
    return "Subject performance is stable; continue regular monitoring."


def get_teacher_activity_recommendation(activity_status):
    if activity_status == "inactive":
        return "Follow up with the teacher to start using assignments for their classes."
    if activity_status == "low_activity":
        return "Encourage the teacher to publish more topic-based assignments."
    return "Teacher activity is healthy; continue monitoring outcomes."
