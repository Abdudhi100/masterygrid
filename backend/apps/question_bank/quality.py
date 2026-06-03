from collections import Counter, defaultdict

from django.db.models import Count, Q

from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question
from apps.question_bank.selectors import is_platform_admin


QUALITY_SECTION_KEYS = [
    "needs_manual_review",
    "missing_explanations",
    "diagram_issues",
    "duplicate_suspects",
    "imported_drafts",
    "ready_for_approval",
    "metadata_issues",
]


def normalize_question_text(value):
    return " ".join(str(value or "").strip().split()).casefold()


def question_quality_queryset(user, params=None):
    params = params or {}
    queryset = Question.objects.select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
        "created_by",
    ).prefetch_related(
        "media",
        "options",
        "import_rows",
        "import_rows__batch",
    )

    if is_platform_admin(user):
        school_id = params.get("school")
        if school_id:
            queryset = queryset.filter(school_id=school_id)
    elif user and user.is_authenticated and user.role == UserRole.SCHOOL_ADMIN:
        queryset = queryset.filter(school=user.school)
    else:
        return queryset.none()

    for field in ["subject", "topic", "class_level", "status"]:
        value = params.get(field)
        if value:
            queryset = queryset.filter(**{field: value})

    source_type = params.get("source_type")
    if source_type:
        queryset = queryset.filter(source__source_type=source_type)

    return queryset.annotate(
        option_count=Count("options", distinct=True),
        correct_option_count=Count(
            "options",
            filter=Q(options__is_correct=True),
            distinct=True,
        ),
        active_media_count=Count(
            "media",
            filter=Q(media__is_active=True),
            distinct=True,
        ),
        media_manual_review_count=Count(
            "media",
            filter=Q(media__is_active=True, media__needs_manual_review=True),
            distinct=True,
        ),
        import_row_count=Count("import_rows", distinct=True),
    )


def has_missing_explanation(question):
    return not (question.explanation or "").strip()


def diagram_issue_message(question):
    messages = []
    active_media_count = getattr(question, "active_media_count", None)
    media_review_count = getattr(question, "media_manual_review_count", None)
    if active_media_count is None:
        active_media_count = question.media.filter(is_active=True).count()
    if media_review_count is None:
        media_review_count = question.media.filter(
            is_active=True,
            needs_manual_review=True,
        ).count()

    if question.needs_manual_review:
        messages.append("Question is marked for manual review.")
    if question.has_diagram and active_media_count == 0:
        messages.append("Question is marked as having a diagram but has no active media.")
    if question.has_diagram and not (question.diagram_description or "").strip():
        messages.append("Diagram description is missing.")
    if media_review_count:
        messages.append("One or more media items need manual review.")

    return " ".join(messages)


def has_metadata_issue(question):
    return (
        not question.subject_id
        or not question.topic_id
        or not question.class_level_id
        or not question.difficulty
        or not question.source_id
    )


def metadata_issue_message(question):
    missing = []
    if not question.subject_id:
        missing.append("subject")
    if not question.topic_id:
        missing.append("topic")
    if not question.class_level_id:
        missing.append("class level")
    if not question.difficulty:
        missing.append("difficulty")
    if not question.source_id:
        missing.append("source")
    return f"Missing metadata: {', '.join(missing)}." if missing else ""


def ready_for_approval_message(question):
    option_count = getattr(question, "option_count", question.options.count())
    correct_count = getattr(
        question,
        "correct_option_count",
        question.options.filter(is_correct=True).count(),
    )
    diagram_message = diagram_issue_message(question)
    failures = []
    if question.status != QuestionStatus.DRAFT:
        failures.append("Question is not draft.")
    if option_count != 4:
        failures.append("Question must have exactly four options.")
    if correct_count != 1:
        failures.append("Question must have exactly one correct option.")
    if not question.subject_id:
        failures.append("Subject is missing.")
    if not question.topic_id:
        failures.append("Topic is missing.")
    if not question.class_level_id:
        failures.append("Class level is missing.")
    if not question.difficulty:
        failures.append("Difficulty is missing.")
    if has_missing_explanation(question):
        failures.append("Explanation is missing.")
    if diagram_message:
        failures.append(diagram_message)
    return " ".join(failures)


def is_ready_for_approval(question):
    return not ready_for_approval_message(question)


def first_import_row(question):
    rows = list(question.import_rows.all())
    if not rows:
        return None
    return sorted(rows, key=lambda row: row.row_number)[0]


def quality_row(question, *, issue_type, issue_message):
    import_row = first_import_row(question)
    source = question.source
    return {
        "id": question.id,
        "question_preview": (question.question_text or "")[:180],
        "subject_id": question.subject_id,
        "subject_name": getattr(question.subject, "name", ""),
        "topic_id": question.topic_id,
        "topic_title": getattr(question.topic, "title", ""),
        "class_level_id": question.class_level_id,
        "class_level_name": getattr(question.class_level, "name", ""),
        "difficulty": question.difficulty,
        "status": question.status,
        "source_id": question.source_id,
        "source_name": getattr(source, "name", "") if source else "",
        "source_type": getattr(source, "source_type", "") if source else "",
        "year": getattr(source, "year", None) if source else None,
        "has_diagram": question.has_diagram,
        "media_count": getattr(question, "active_media_count", 0),
        "needs_manual_review": question.needs_manual_review,
        "issue_type": issue_type,
        "issue_message": issue_message,
        "created_at": question.created_at,
        "created_by": question.created_by_id,
        "created_by_name": getattr(question.created_by, "full_name", "") or "",
        "import_batch_id": import_row.batch_id if import_row else None,
        "import_batch_title": import_row.batch.title if import_row else "",
        "action_url": f"/admin/question-bank/{question.id}",
        "ai_suggestion_url": f"/admin/question-bank/{question.id}#ai-suggestions",
    }


def build_duplicate_maps(questions):
    by_hash = defaultdict(list)
    text_counter = Counter()
    for question in questions:
        if question.content_hash:
            by_hash[question.content_hash].append(question.id)
        normalized_text = normalize_question_text(question.question_text)
        if normalized_text:
            text_counter[normalized_text] += 1
    duplicate_hash_ids = {
        question_id
        for ids in by_hash.values()
        if len(ids) > 1
        for question_id in ids
    }
    duplicate_texts = {text for text, count in text_counter.items() if count > 1}
    return duplicate_hash_ids, duplicate_texts


def build_question_quality_dashboard(*, user, params=None):
    params = params or {}
    limit = min(int(params.get("limit") or 25), 100)
    issue_type = params.get("issue_type") or ""
    queryset = question_quality_queryset(user, params)
    questions = list(queryset)
    duplicate_hash_ids, duplicate_texts = build_duplicate_maps(questions)

    sections = {key: [] for key in QUALITY_SECTION_KEYS}
    summary = {
        "total_questions": len(questions),
        "approved_count": 0,
        "draft_count": 0,
        "rejected_count": 0,
        "archived_count": 0,
        "needs_manual_review_count": 0,
        "missing_explanation_count": 0,
        "missing_topic_count": 0,
        "missing_difficulty_count": 0,
        "diagram_issue_count": 0,
        "duplicate_suspect_count": 0,
        "ready_for_review_count": 0,
    }

    for question in questions:
        if question.status == QuestionStatus.APPROVED:
            summary["approved_count"] += 1
        elif question.status == QuestionStatus.DRAFT:
            summary["draft_count"] += 1
        elif question.status == QuestionStatus.REJECTED:
            summary["rejected_count"] += 1
        elif question.status == QuestionStatus.ARCHIVED:
            summary["archived_count"] += 1

        if question.needs_manual_review:
            summary["needs_manual_review_count"] += 1
            sections["needs_manual_review"].append(
                quality_row(
                    question,
                    issue_type="needs_manual_review",
                    issue_message="Question is marked for manual review.",
                )
            )

        if has_missing_explanation(question):
            summary["missing_explanation_count"] += 1
            sections["missing_explanations"].append(
                quality_row(
                    question,
                    issue_type="missing_explanation",
                    issue_message="Question explanation is missing.",
                )
            )

        if not question.topic_id:
            summary["missing_topic_count"] += 1
        if not question.difficulty:
            summary["missing_difficulty_count"] += 1

        diagram_message = diagram_issue_message(question)
        if diagram_message:
            summary["diagram_issue_count"] += 1
            sections["diagram_issues"].append(
                quality_row(
                    question,
                    issue_type="diagram_issue",
                    issue_message=diagram_message,
                )
            )

        normalized_text = normalize_question_text(question.question_text)
        is_duplicate = question.id in duplicate_hash_ids or normalized_text in duplicate_texts
        if is_duplicate:
            summary["duplicate_suspect_count"] += 1
            sections["duplicate_suspects"].append(
                quality_row(
                    question,
                    issue_type="duplicate_suspect",
                    issue_message="Question appears to duplicate another question.",
                )
            )

        if question.status == QuestionStatus.DRAFT and getattr(question, "import_row_count", 0):
            sections["imported_drafts"].append(
                quality_row(
                    question,
                    issue_type="imported_draft",
                    issue_message="Imported question is still in draft status.",
                )
            )

        if has_metadata_issue(question):
            sections["metadata_issues"].append(
                quality_row(
                    question,
                    issue_type="metadata_issue",
                    issue_message=metadata_issue_message(question),
                )
            )

        if question.status == QuestionStatus.DRAFT and is_ready_for_approval(question):
            summary["ready_for_review_count"] += 1
            sections["ready_for_approval"].append(
                quality_row(
                    question,
                    issue_type="ready_for_approval",
                    issue_message="Draft question passes quality checks and is ready for approval.",
                )
            )

    for key in sections:
        sections[key] = sorted(
            sections[key],
            key=lambda row: row["created_at"],
            reverse=True,
        )[:limit]

    if issue_type and issue_type in sections:
        filtered_sections = {key: [] for key in QUALITY_SECTION_KEYS}
        filtered_sections[issue_type] = sections[issue_type]
        sections = filtered_sections

    return {
        "summary": summary,
        "sections": sections,
        "filters": {
            "limit": limit,
            "issue_type": issue_type,
            "subject": params.get("subject") or "",
            "topic": params.get("topic") or "",
            "class_level": params.get("class_level") or "",
            "status": params.get("status") or "",
            "source_type": params.get("source_type") or "",
            "school": params.get("school") or "",
        },
    }
