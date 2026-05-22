from collections import defaultdict

from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404

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
from apps.common.choices import AssignmentStatus, SubmissionStatus
from apps.submissions.models import Submission


LOW_SCORE_THRESHOLD = 40
WEAK_TOPIC_THRESHOLD = 50


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
