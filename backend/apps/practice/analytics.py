from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, Q

from apps.common.choices import QuestionStatus
from apps.practice.models import PracticeSession, PracticeSessionStatus
from apps.question_bank.models import Question


MIN_TOPIC_ANSWER_COUNT = 5
MIN_TOPIC_SESSION_COUNT = 2


def _submitted_sessions(student):
    if not student or not student.is_authenticated or not student.school_id:
        return PracticeSession.objects.none()

    return (
        PracticeSession.objects.filter(
            school=student.school,
            student=student,
            status=PracticeSessionStatus.SUBMITTED,
        )
        .select_related("subject", "topic", "class_level", "class_arm")
        .prefetch_related("answers")
        .order_by("-submitted_at", "-created_at")
    )


def _to_float(value):
    if value is None:
        return None
    return float(value)


def _weighted_percentage(score, total_marks):
    if not total_marks:
        return None
    percentage = (
        Decimal(score) / Decimal(total_marks) * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(percentage)


def _strength_level(average_percentage):
    if average_percentage is None:
        return "average"
    if average_percentage >= 70:
        return "strong"
    if average_percentage >= 50:
        return "average"
    return "weak"


def _meets_topic_threshold(row):
    return (
        row["questions_answered"] >= MIN_TOPIC_ANSWER_COUNT
        or row["sessions_completed"] >= MIN_TOPIC_SESSION_COUNT
    )


def _submitted_sessions_with_answers(student):
    return _submitted_sessions(student).prefetch_related(
        "answers",
        "answers__session_question",
    )


def get_student_practice_summary(student):
    sessions = list(_submitted_sessions_with_answers(student))
    total_sessions = len(sessions)
    total_score = sum(session.score for session in sessions)
    total_marks = sum(session.total_marks for session in sessions)
    total_questions_answered = sum(session.answers.count() for session in sessions)
    total_correct_answers = sum(
        session.answers.filter(is_correct=True).count() for session in sessions
    )

    percentages = [
        session.percentage
        for session in sessions
        if session.percentage is not None
    ]
    subject_performance = get_student_subject_performance(student)
    best_subject = None
    weakest_subject = None
    if subject_performance:
        best_subject = sorted(
            subject_performance,
            key=lambda row: row["average_percentage"] or 0,
            reverse=True,
        )[0]["subject_name"]
        weakest_subject = sorted(
            subject_performance,
            key=lambda row: row["average_percentage"] if row["average_percentage"] is not None else 101,
        )[0]["subject_name"]

    return {
        "total_sessions_completed": total_sessions,
        "total_questions_answered": total_questions_answered,
        "total_correct_answers": total_correct_answers,
        "overall_average_percentage": _weighted_percentage(total_score, total_marks),
        "best_percentage": _to_float(max(percentages)) if percentages else None,
        "lowest_percentage": _to_float(min(percentages)) if percentages else None,
        "last_practice_at": sessions[0].submitted_at if sessions else None,
        "best_subject": best_subject,
        "weakest_subject": weakest_subject,
    }


def get_student_subject_performance(student):
    grouped = {}
    for session in _submitted_sessions_with_answers(student):
        subject_id = session.subject_id
        if subject_id not in grouped:
            grouped[subject_id] = {
                "subject_id": subject_id,
                "subject_name": session.subject.name,
                "sessions_completed": 0,
                "questions_answered": 0,
                "correct_answers": 0,
                "score": 0,
                "total_marks": 0,
                "last_practiced_at": None,
            }

        row = grouped[subject_id]
        row["sessions_completed"] += 1
        row["questions_answered"] += session.answers.count()
        row["correct_answers"] += session.answers.filter(is_correct=True).count()
        row["score"] += session.score
        row["total_marks"] += session.total_marks
        if (
            row["last_practiced_at"] is None
            or (
                session.submitted_at is not None
                and session.submitted_at > row["last_practiced_at"]
            )
        ):
            row["last_practiced_at"] = session.submitted_at

    results = []
    for row in grouped.values():
        total_marks = row.pop("total_marks")
        score = row.pop("score")
        row["average_percentage"] = _weighted_percentage(score, total_marks)
        results.append(row)

    return sorted(
        results,
        key=lambda row: row["average_percentage"] if row["average_percentage"] is not None else -1,
        reverse=True,
    )


def get_student_topic_performance(student):
    grouped = {}
    for session in _submitted_sessions_with_answers(student):
        if not session.topic_id:
            continue

        topic_id = session.topic_id
        if topic_id not in grouped:
            grouped[topic_id] = {
                "topic_id": topic_id,
                "topic_title": session.topic.title,
                "subject_id": session.subject_id,
                "subject_name": session.subject.name,
                "sessions_completed": 0,
                "questions_answered": 0,
                "correct_answers": 0,
                "score": 0,
                "total_marks": 0,
                "last_practiced_at": None,
            }

        row = grouped[topic_id]
        row["sessions_completed"] += 1
        row["questions_answered"] += session.answers.count()
        row["correct_answers"] += session.answers.filter(is_correct=True).count()
        row["score"] += session.score
        row["total_marks"] += session.total_marks
        if (
            row["last_practiced_at"] is None
            or (
                session.submitted_at is not None
                and session.submitted_at > row["last_practiced_at"]
            )
        ):
            row["last_practiced_at"] = session.submitted_at

    results = []
    for row in grouped.values():
        total_marks = row.pop("total_marks")
        score = row.pop("score")
        row["average_percentage"] = _weighted_percentage(score, total_marks)
        row["strength_level"] = _strength_level(row["average_percentage"])
        results.append(row)

    return sorted(
        results,
        key=lambda row: row["average_percentage"] if row["average_percentage"] is not None else -1,
        reverse=True,
    )


def get_student_recent_practice(student, limit=10):
    sessions = _submitted_sessions(student)[:limit]
    return [
        {
            "id": session.id,
            "subject_id": session.subject_id,
            "subject_name": session.subject.name,
            "topic_id": session.topic_id,
            "topic_title": session.topic.title if session.topic_id else None,
            "difficulty": session.difficulty,
            "question_count_requested": session.question_count_requested,
            "score": session.score,
            "total_marks": session.total_marks,
            "percentage": _to_float(session.percentage),
            "started_at": session.started_at,
            "submitted_at": session.submitted_at,
        }
        for session in sessions
    ]


def get_student_weak_topics(student, limit=5):
    weak_topics = [
        row
        for row in get_student_topic_performance(student)
        if row["average_percentage"] is not None
        and row["average_percentage"] < 50
        and _meets_topic_threshold(row)
    ]
    return sorted(
        weak_topics,
        key=lambda row: (row["average_percentage"], -row["questions_answered"]),
    )[:limit]


def get_student_strong_topics(student, limit=5):
    strong_topics = [
        row
        for row in get_student_topic_performance(student)
        if row["average_percentage"] is not None
        and row["average_percentage"] >= 70
        and _meets_topic_threshold(row)
    ]
    return sorted(
        strong_topics,
        key=lambda row: (-row["average_percentage"], -row["questions_answered"]),
    )[:limit]


def _approved_question_counts_by_topic(student):
    if not student or not student.is_authenticated or not student.school_id:
        return {}

    rows = (
        Question.objects.filter(
            Q(school__isnull=True) | Q(school=student.school),
            status=QuestionStatus.APPROVED,
            is_active=True,
            topic__isnull=False,
        )
        .values(
            "topic_id",
            "topic__title",
            "subject_id",
            "subject__name",
        )
        .annotate(available_question_count=Count("id"))
        .order_by("subject__name", "topic__title")
    )

    return {
        row["topic_id"]: {
            "topic_id": row["topic_id"],
            "topic_title": row["topic__title"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject__name"],
            "available_question_count": row["available_question_count"],
        }
        for row in rows
        if row["available_question_count"] > 0
    }


def _recommended_difficulty(average_percentage):
    if average_percentage is None:
        return "easy"
    if average_percentage < 50:
        return "easy"
    if average_percentage < 70:
        return "medium"
    return "hard"


def _suggested_question_count(available_count):
    return max(1, min(10, available_count))


def _recommendation_from_performance(row, availability, priority, reason):
    average_percentage = row.get("average_percentage")
    return {
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"],
        "topic_id": row["topic_id"],
        "topic_title": row["topic_title"],
        "priority": priority,
        "reason": reason,
        "recommended_difficulty": _recommended_difficulty(average_percentage),
        "available_question_count": availability["available_question_count"],
        "suggested_question_count": _suggested_question_count(
            availability["available_question_count"]
        ),
    }


def get_student_practice_recommendations(student, limit=5):
    availability_by_topic = _approved_question_counts_by_topic(student)
    recommendations = []
    used_topic_ids = set()

    for row in get_student_weak_topics(student, limit=limit * 2):
        availability = availability_by_topic.get(row["topic_id"])
        if not availability:
            continue
        recommendations.append(
            _recommendation_from_performance(
                row,
                availability,
                "high",
                (
                    f"You scored {row['average_percentage']:.2f}% across "
                    f"{row['questions_answered']} practice question(s)."
                ),
            )
        )
        used_topic_ids.add(row["topic_id"])
        if len(recommendations) >= limit:
            return recommendations

    average_topics = [
        row
        for row in get_student_topic_performance(student)
        if row["topic_id"] not in used_topic_ids
        and row["average_percentage"] is not None
        and 50 <= row["average_percentage"] < 70
    ]
    average_topics = sorted(
        average_topics,
        key=lambda row: (row["average_percentage"], -row["questions_answered"]),
    )
    for row in average_topics:
        availability = availability_by_topic.get(row["topic_id"])
        if not availability:
            continue
        recommendations.append(
            _recommendation_from_performance(
                row,
                availability,
                "medium",
                (
                    f"You are averaging {row['average_percentage']:.2f}% on "
                    "this topic. More practice can make it stronger."
                ),
            )
        )
        used_topic_ids.add(row["topic_id"])
        if len(recommendations) >= limit:
            return recommendations

    practiced_topic_ids = {
        row["topic_id"] for row in get_student_topic_performance(student)
    }
    unpracticed_topics = [
        row
        for topic_id, row in availability_by_topic.items()
        if topic_id not in practiced_topic_ids and topic_id not in used_topic_ids
    ]
    for row in unpracticed_topics:
        recommendations.append(
            {
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"],
                "topic_id": row["topic_id"],
                "topic_title": row["topic_title"],
                "priority": "low",
                "reason": "You have not practised this topic yet.",
                "recommended_difficulty": "easy",
                "available_question_count": row["available_question_count"],
                "suggested_question_count": _suggested_question_count(
                    row["available_question_count"]
                ),
            }
        )
        if len(recommendations) >= limit:
            break

    return recommendations


def get_student_practice_dashboard(student):
    summary = get_student_practice_summary(student)
    has_history = summary["total_sessions_completed"] > 0
    return {
        "summary": summary,
        "subject_performance": get_student_subject_performance(student),
        "topic_performance": get_student_topic_performance(student),
        "weak_topics": get_student_weak_topics(student),
        "strong_topics": get_student_strong_topics(student),
        "recommendations": get_student_practice_recommendations(student),
        "recent_sessions": get_student_recent_practice(student),
        "message": (
            ""
            if has_history
            else "Complete a practice session to unlock personalized analytics."
        ),
    }
