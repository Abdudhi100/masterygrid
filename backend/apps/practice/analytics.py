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


def get_student_weak_topics(student, limit=5, topic_performance=None):
    rows = (
        topic_performance
        if topic_performance is not None
        else get_student_topic_performance(student)
    )
    weak_topics = [
        row
        for row in rows
        if row["average_percentage"] is not None
        and row["average_percentage"] < 50
        and _meets_topic_threshold(row)
    ]
    return sorted(
        weak_topics,
        key=lambda row: (row["average_percentage"], -row["questions_answered"]),
    )[:limit]


def get_student_strong_topics(student, limit=5, topic_performance=None):
    rows = (
        topic_performance
        if topic_performance is not None
        else get_student_topic_performance(student)
    )
    strong_topics = [
        row
        for row in rows
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

    base_queryset = Question.objects.filter(
        Q(school__isnull=True) | Q(school=student.school),
        status=QuestionStatus.APPROVED,
        is_active=True,
        topic__isnull=False,
    )

    rows = (
        base_queryset
        .values(
            "topic_id",
            "topic__title",
            "topic__class_level_id",
            "topic__class_level__name",
            "subject_id",
            "subject__name",
        )
        .annotate(available_question_count=Count("id"))
        .order_by("subject__name", "topic__title", "topic_id")
    )

    availability = {
        row["topic_id"]: {
            "topic_id": row["topic_id"],
            "topic_title": row["topic__title"],
            "class_level_id": row["topic__class_level_id"],
            "class_level_name": row["topic__class_level__name"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject__name"],
            "available_question_count": row["available_question_count"],
            "counts_by_difficulty": {},
        }
        for row in rows
        if row["available_question_count"] > 0
    }

    difficulty_rows = (
        base_queryset.values("topic_id", "difficulty")
        .annotate(question_count=Count("id"))
        .order_by("topic_id", "difficulty")
    )
    for row in difficulty_rows:
        topic_availability = availability.get(row["topic_id"])
        if not topic_availability:
            continue
        topic_availability["counts_by_difficulty"][row["difficulty"]] = row[
            "question_count"
        ]

    return availability


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


def _available_count_for_difficulty(availability, difficulty):
    if difficulty == "mixed":
        return availability["available_question_count"]
    return availability.get("counts_by_difficulty", {}).get(difficulty, 0)


def _recommended_difficulty_for_availability(average_percentage, availability):
    preferred_difficulty = _recommended_difficulty(average_percentage)
    if _available_count_for_difficulty(availability, preferred_difficulty) > 0:
        return preferred_difficulty
    return "mixed"


def _recommended_question_count_for_difficulty(availability, difficulty):
    return _suggested_question_count(
        _available_count_for_difficulty(availability, difficulty)
    )


def _recommendation_from_performance(row, availability, priority, reason):
    average_percentage = row.get("average_percentage")
    recommended_difficulty = _recommended_difficulty(average_percentage)
    return {
        "subject_id": row["subject_id"],
        "subject_name": row["subject_name"],
        "topic_id": row["topic_id"],
        "topic_title": row["topic_title"],
        "priority": priority,
        "reason": reason,
        "recommended_difficulty": recommended_difficulty,
        "available_question_count": availability["available_question_count"],
        "suggested_question_count": _suggested_question_count(
            availability["available_question_count"]
        ),
    }


def get_student_practice_recommendations(student, limit=5, topic_performance=None):
    availability_by_topic = _approved_question_counts_by_topic(student)
    if topic_performance is None:
        topic_performance = get_student_topic_performance(student)
    recommendations = []
    used_topic_ids = set()

    for row in get_student_weak_topics(
        student,
        limit=limit * 2,
        topic_performance=topic_performance,
    ):
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
        for row in topic_performance
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
        row["topic_id"] for row in topic_performance
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


def _topic_performance_summary(row=None):
    if not row:
        return {
            "sessions_completed": 0,
            "questions_answered": 0,
            "correct_answers": 0,
            "average_percentage": None,
            "strength_level": "new",
            "last_practiced_at": None,
        }

    return {
        "sessions_completed": row["sessions_completed"],
        "questions_answered": row["questions_answered"],
        "correct_answers": row["correct_answers"],
        "average_percentage": row["average_percentage"],
        "strength_level": row["strength_level"],
        "last_practiced_at": row["last_practiced_at"],
    }


def _learning_path_reason(category, row=None):
    if category == "weak_topic":
        return (
            f"Your average is {row['average_percentage']:.2f}% across "
            f"{row['questions_answered']} question(s). Start with focused review."
        )
    if category == "needs_reinforcement":
        return (
            f"You are averaging {row['average_percentage']:.2f}%. A short "
            "reinforcement set can move this into a strong area."
        )
    if category == "challenge":
        return (
            f"You are averaging {row['average_percentage']:.2f}%. Try a harder "
            "set to keep this topic sharp."
        )
    return "You have not practised this topic yet, but approved questions are available."


def _learning_path_card(
    *,
    rank,
    category,
    priority,
    availability,
    performance=None,
):
    average_percentage = (
        performance["average_percentage"] if performance is not None else None
    )
    recommended_difficulty = _recommended_difficulty_for_availability(
        average_percentage,
        availability,
    )
    recommended_question_count = _recommended_question_count_for_difficulty(
        availability,
        recommended_difficulty,
    )
    action_payload = {
        "subject": availability["subject_id"],
        "topic": availability["topic_id"],
        "class_level": availability["class_level_id"],
        "difficulty": recommended_difficulty,
        "question_count": recommended_question_count,
    }

    return {
        "rank": rank,
        "category": category,
        "priority": priority,
        "reason": _learning_path_reason(category, performance),
        "subject_id": availability["subject_id"],
        "subject_name": availability["subject_name"],
        "topic_id": availability["topic_id"],
        "topic_title": availability["topic_title"],
        "class_level_id": availability["class_level_id"],
        "class_level_name": availability["class_level_name"],
        "difficulty": recommended_difficulty,
        "recommended_question_count": recommended_question_count,
        "available_question_count": availability["available_question_count"],
        "performance": _topic_performance_summary(performance),
        "action_payload": action_payload,
    }


def _learning_path_overall_status(summary, cards):
    if not cards:
        return {
            "overall_status": "no_questions_available",
            "headline": "No approved practice questions yet",
            "message": (
                "Ask your teacher or school admin to approve question-bank "
                "questions before starting a learning path."
            ),
        }

    if summary["total_sessions_completed"] == 0:
        return {
            "overall_status": "getting_started",
            "headline": "Start your guided practice path",
            "message": (
                "Begin with an available topic. Your path will become more "
                "personalized after you submit practice sessions."
            ),
        }

    first_category = cards[0]["category"]
    if first_category == "weak_topic":
        return {
            "overall_status": "needs_attention",
            "headline": "Focus on your weakest topic next",
            "message": (
                "Your path is prioritizing topics where recent practice shows "
                "the biggest support need."
            ),
        }
    if first_category == "needs_reinforcement":
        return {
            "overall_status": "building_consistency",
            "headline": "Build consistency with reinforcement practice",
            "message": (
                "You are close to strong performance on the next topic. A "
                "focused set should help."
            ),
        }

    return {
        "overall_status": "on_track",
        "headline": "Keep building with the next best topic",
        "message": (
            "Your path is balancing new topics and challenge practice from "
            "approved question-bank questions."
        ),
    }


def get_student_learning_path(student, limit=8):
    summary = get_student_practice_summary(student)
    availability_by_topic = _approved_question_counts_by_topic(student)
    topic_performance = get_student_topic_performance(student)
    performance_by_topic = {
        row["topic_id"]: row
        for row in topic_performance
    }
    cards = []
    used_topic_ids = set()

    def add_card(category, priority, availability, performance=None):
        if availability["topic_id"] in used_topic_ids or len(cards) >= limit:
            return
        cards.append(
            _learning_path_card(
                rank=len(cards) + 1,
                category=category,
                priority=priority,
                availability=availability,
                performance=performance,
            )
        )
        used_topic_ids.add(availability["topic_id"])

    for row in get_student_weak_topics(
        student,
        limit=limit * 2,
        topic_performance=topic_performance,
    ):
        availability = availability_by_topic.get(row["topic_id"])
        if availability:
            add_card("weak_topic", "high", availability, row)

    average_topics = [
        row
        for row in topic_performance
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
        if availability:
            add_card("needs_reinforcement", "medium", availability, row)

    unpracticed_topics = [
        row
        for row in availability_by_topic.values()
        if row["topic_id"] not in performance_by_topic
        and row["topic_id"] not in used_topic_ids
    ]
    unpracticed_topics = sorted(
        unpracticed_topics,
        key=lambda row: (row["subject_name"], row["topic_title"], row["topic_id"]),
    )
    for availability in unpracticed_topics:
        add_card("new_topic", "low", availability)

    for row in get_student_strong_topics(
        student,
        limit=limit * 2,
        topic_performance=topic_performance,
    ):
        availability = availability_by_topic.get(row["topic_id"])
        if availability:
            add_card("challenge", "low", availability, row)

    status = _learning_path_overall_status(summary, cards)
    return {
        **status,
        "recommended_next_action": cards[0] if cards else None,
        "topic_cards": cards,
        "summary": summary,
    }


def get_student_practice_dashboard(student):
    summary = get_student_practice_summary(student)
    topic_performance = get_student_topic_performance(student)
    has_history = summary["total_sessions_completed"] > 0
    return {
        "summary": summary,
        "subject_performance": get_student_subject_performance(student),
        "topic_performance": topic_performance,
        "weak_topics": get_student_weak_topics(
            student,
            topic_performance=topic_performance,
        ),
        "strong_topics": get_student_strong_topics(
            student,
            topic_performance=topic_performance,
        ),
        "recommendations": get_student_practice_recommendations(
            student,
            topic_performance=topic_performance,
        ),
        "recent_sessions": get_student_recent_practice(student),
        "message": (
            ""
            if has_history
            else "Complete a practice session to unlock personalized analytics."
        ),
    }
