import csv
import hashlib
import io

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.academics.models import ClassLevel, Subject, Topic
from apps.common.choices import QuestionStatus, UserRole
from apps.common.constants import JAMB_MVP_OPTION_COUNT
from apps.question_bank.models import (
    Question,
    QuestionDifficulty,
    QuestionImportBatchStatus,
    QuestionImportRow,
    QuestionImportRowStatus,
    QuestionMedia,
    QuestionMediaType,
    QuestionOption,
    QuestionOptionLabel,
    QuestionSource,
    QuestionSourceType,
)


EXPECTED_OPTION_LABELS = {"A", "B", "C", "D"}
CSV_IMPORT_COLUMNS = {
    "subject",
    "class_level",
    "topic",
    "source_name",
    "source_type",
    "exam_body",
    "year",
    "difficulty",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
    "explanation",
}
CSV_IMPORT_OPTIONAL_COLUMNS = {
    "has_diagram",
    "diagram_file_name",
    "diagram_url",
    "diagram_description",
    "needs_manual_review",
}
BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "y"}
BOOLEAN_FALSE_VALUES = {"0", "false", "no", "n", ""}


class DuplicateQuestionError(Exception):
    def __init__(self, message, content_hash=""):
        super().__init__(message)
        self.content_hash = content_hash


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(user, "is_superuser", False)
        )
    )


def normalize_question_text(text):
    return " ".join(str(text or "").strip().split())


def normalize_hash_part(value):
    return normalize_question_text(value).casefold()


def build_question_content_hash(*, question_text, subject, topic, class_level, options):
    option_parts = []
    for option in sorted(options, key=lambda item: item["label"]):
        option_parts.append(
            f"{option['label'].upper()}:{normalize_hash_part(option['text'])}"
        )

    parts = [
        normalize_hash_part(question_text),
        str(getattr(subject, "id", subject)),
        str(getattr(topic, "id", topic)),
        str(getattr(class_level, "id", class_level)),
        "|".join(option_parts),
    ]
    return hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()


def load_csv_import_rows(uploaded_file):
    uploaded_file.seek(0)
    raw_content = uploaded_file.read()
    if isinstance(raw_content, str):
        text_content = raw_content
    else:
        text_content = raw_content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text_content))
    if not reader.fieldnames:
        raise ValidationError({"file": "CSV file must include a header row."})

    normalized_fieldnames = [normalize_hash_part(field) for field in reader.fieldnames]
    missing_columns = sorted(CSV_IMPORT_COLUMNS - set(normalized_fieldnames))
    if missing_columns:
        raise ValidationError(
            {"file": f"CSV is missing required column(s): {', '.join(missing_columns)}."}
        )

    rows = []
    for line_number, row in enumerate(reader, start=2):
        normalized_row = {}
        for key, value in row.items():
            normalized_key = normalize_hash_part(key)
            normalized_row[normalized_key] = "" if value is None else str(value).strip()

        if any(value for value in normalized_row.values()):
            rows.append((line_number, normalized_row))

    return rows


def create_pending_import_rows(batch, rows):
    QuestionImportRow.objects.filter(batch=batch).delete()
    import_rows = [
        QuestionImportRow(batch=batch, row_number=row_number, raw_data=row_data)
        for row_number, row_data in rows
    ]
    QuestionImportRow.objects.bulk_create(import_rows)
    batch.total_rows = len(import_rows)
    batch.save(update_fields=["total_rows", "updated_at"])
    return import_rows


def validate_question_options(options):
    if len(options) != JAMB_MVP_OPTION_COUNT:
        raise ValidationError(
            {"options": f"Exactly {JAMB_MVP_OPTION_COUNT} options are required."}
        )

    labels = [option.get("label") for option in options]
    label_set = set(labels)
    if label_set != EXPECTED_OPTION_LABELS:
        raise ValidationError({"options": "Options must use labels A, B, C, and D."})

    correct_count = sum(1 for option in options if option.get("is_correct") is True)
    if correct_count != 1:
        raise ValidationError({"options": "Exactly one option must be marked correct."})

    normalized_texts = []
    for option in options:
        text = option.get("text", "")
        if not text or not text.strip():
            raise ValidationError({"options": "Option text cannot be blank."})
        normalized_texts.append(text.strip().casefold())

    if len(normalized_texts) != len(set(normalized_texts)):
        raise ValidationError(
            {"options": "Duplicate option text is not allowed for the same question."}
        )


def validation_error_message(exc):
    if hasattr(exc, "message_dict"):
        parts = []
        for field, messages in exc.message_dict.items():
            if isinstance(messages, (list, tuple)):
                parts.append(f"{field}: {' '.join(str(message) for message in messages)}")
            else:
                parts.append(f"{field}: {messages}")
        return " ".join(parts)

    messages = getattr(exc, "messages", None)
    if messages:
        return " ".join(str(message) for message in messages)

    return str(exc)


def get_required_row_value(row_data, field):
    value = normalize_question_text(row_data.get(field, ""))
    if not value:
        raise ValidationError({field: "This field is required."})
    return value


def get_optional_row_value(row_data, field):
    return normalize_question_text(row_data.get(field, ""))


def parse_optional_year(value):
    value = normalize_question_text(value)
    if not value:
        return None

    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({"year": "Year must be a number."}) from exc

    if year < 1900 or year > timezone.now().year + 1:
        raise ValidationError({"year": "Year is outside the supported range."})

    return year


def parse_optional_bool(value, *, field):
    normalized_value = normalize_question_text(value).casefold()
    if normalized_value in BOOLEAN_TRUE_VALUES:
        return True
    if normalized_value in BOOLEAN_FALSE_VALUES:
        return False
    raise ValidationError({field: "Use true/false, yes/no, or 1/0."})


def validate_external_diagram_url(value):
    url = get_optional_row_value({"diagram_url": value}, "diagram_url")
    if not url:
        return ""

    validator = URLValidator(schemes=["http", "https"])
    try:
        validator(url)
    except ValidationError as exc:
        raise ValidationError({"diagram_url": "Enter a valid diagram URL."}) from exc
    return url


def find_visible_subject(*, name, school):
    queryset = Subject.objects.filter(name__iexact=name, is_active=True)
    if school:
        queryset = queryset.filter(Q(school__isnull=True) | Q(school=school))
    else:
        queryset = queryset.filter(school__isnull=True)

    subject = queryset.order_by("school_id").first()
    if not subject:
        raise ValidationError({"subject": f"Subject '{name}' was not found."})
    return subject


def find_visible_class_level(*, name, school):
    queryset = ClassLevel.objects.filter(name__iexact=name, is_active=True)
    if school:
        queryset = queryset.filter(school=school)
    else:
        if queryset.count() > 1:
            raise ValidationError(
                {
                    "class_level": (
                        f"Class level '{name}' exists in multiple schools. "
                        "Use a school-specific import."
                    )
                }
            )

    class_level = queryset.first()
    if not class_level:
        raise ValidationError({"class_level": f"Class level '{name}' was not found."})
    return class_level


def find_visible_topic(*, title, subject, class_level, school):
    queryset = Topic.objects.filter(
        title__iexact=title,
        subject=subject,
        class_level=class_level,
        is_active=True,
    )
    if school:
        queryset = queryset.filter(Q(school__isnull=True) | Q(school=school)).order_by(
            "-school_id"
        )
    else:
        queryset = queryset.filter(school__isnull=True)

    topic = queryset.first()
    if not topic:
        raise ValidationError(
            {
                "topic": (
                    f"Topic '{title}' was not found for subject '{subject.name}' "
                    f"and class level '{class_level.name}'."
                )
            }
        )
    return topic


def get_or_create_import_source(*, row_data, batch):
    if batch.source_id:
        return batch.source

    source_name = get_required_row_value(row_data, "source_name")
    source_type = get_required_row_value(row_data, "source_type")
    source_type = source_type.lower()
    if source_type not in QuestionSourceType.values:
        raise ValidationError(
            {"source_type": "Source type must be one of the configured source types."}
        )

    exam_body = get_optional_row_value(row_data, "exam_body")
    year = parse_optional_year(row_data.get("year", ""))
    source, _created = QuestionSource.objects.get_or_create(
        name=source_name,
        source_type=source_type,
        year=year,
        defaults={
            "exam_body": exam_body,
            "description": "Created during trusted question import.",
            "is_active": True,
        },
    )

    changed_fields = []
    if exam_body and source.exam_body != exam_body:
        source.exam_body = exam_body
        changed_fields.append("exam_body")
    if not source.is_active:
        source.is_active = True
        changed_fields.append("is_active")
    if changed_fields:
        changed_fields.append("updated_at")
        source.full_clean()
        source.save(update_fields=changed_fields)

    return source


def validate_import_row(row_data, user, batch):
    school = batch.school
    if not is_platform_admin(user) and user.school_id != getattr(school, "id", None):
        raise ValidationError({"school": "Import batch does not belong to your school."})

    subject_name = get_required_row_value(row_data, "subject")
    class_level_name = get_required_row_value(row_data, "class_level")
    topic_title = get_required_row_value(row_data, "topic")
    difficulty = get_required_row_value(row_data, "difficulty").lower()
    question_text = get_required_row_value(row_data, "question_text")
    correct_option = get_required_row_value(row_data, "correct_option").upper()
    explanation = get_optional_row_value(row_data, "explanation")
    has_diagram = parse_optional_bool(
        row_data.get("has_diagram", ""),
        field="has_diagram",
    )
    needs_manual_review = parse_optional_bool(
        row_data.get("needs_manual_review", ""),
        field="needs_manual_review",
    )
    diagram_file_name = get_optional_row_value(row_data, "diagram_file_name")
    diagram_url = validate_external_diagram_url(row_data.get("diagram_url", ""))
    diagram_description = get_optional_row_value(row_data, "diagram_description")

    if difficulty not in QuestionDifficulty.values:
        raise ValidationError({"difficulty": "Difficulty must be easy, medium, or hard."})

    if correct_option not in QuestionOptionLabel.values:
        raise ValidationError({"correct_option": "Correct option must be A, B, C, or D."})

    subject = find_visible_subject(name=subject_name, school=school)
    class_level = find_visible_class_level(name=class_level_name, school=school)
    topic = find_visible_topic(
        title=topic_title,
        subject=subject,
        class_level=class_level,
        school=school,
    )
    source = get_or_create_import_source(row_data=row_data, batch=batch)

    options = []
    for label in ["A", "B", "C", "D"]:
        option_text = get_required_row_value(row_data, f"option_{label.lower()}")
        options.append(
            {
                "label": label,
                "text": option_text,
                "is_correct": label == correct_option,
            }
        )

    validate_question_options(options)
    content_hash = build_question_content_hash(
        question_text=question_text,
        subject=subject,
        topic=topic,
        class_level=class_level,
        options=options,
    )

    if Question.objects.filter(content_hash=content_hash).exists():
        raise DuplicateQuestionError(
            "Exact duplicate question already exists.",
            content_hash=content_hash,
        )

    diagram_requested = has_diagram or bool(diagram_url) or bool(diagram_file_name)
    media = []
    diagram_warning = ""
    if diagram_url:
        media.append(
            {
                "media_type": QuestionMediaType.IMAGE,
                "external_url": diagram_url,
                "original_filename": diagram_file_name,
                "description": diagram_description,
                "alt_text": diagram_description,
                "caption": diagram_description[:255],
                "display_order": 1,
                "is_primary": True,
                "is_active": True,
                "needs_manual_review": needs_manual_review,
            }
        )
    elif diagram_requested:
        needs_manual_review = True
        diagram_warning = (
            "Warning: diagram file must be attached manually; CSV file import "
            "does not attach diagram files yet."
        )

    return {
        "school": school,
        "subject": subject,
        "class_level": class_level,
        "topic": topic,
        "source": source,
        "difficulty": difficulty,
        "question_text": question_text,
        "explanation": explanation,
        "options": options,
        "content_hash": content_hash,
        "has_diagram": diagram_requested,
        "diagram_description": diagram_description,
        "needs_manual_review": needs_manual_review,
        "media": media,
        "diagram_warning": diagram_warning,
    }


@transaction.atomic
def create_question_from_import_row(*, batch, validated_data):
    options = validated_data.pop("options")
    media_items = validated_data.pop("media", [])
    validated_data.pop("diagram_warning", "")
    question = Question(
        **validated_data,
        created_by=batch.uploaded_by,
        status=QuestionStatus.DRAFT,
        is_active=True,
    )
    question.full_clean()
    question.save()

    for option_data in options:
        option = QuestionOption(question=question, **option_data)
        option.full_clean()
        option.save()

    for media_data in media_items:
        media = QuestionMedia(
            question=question,
            created_by=batch.uploaded_by,
            **media_data,
        )
        media.full_clean()
        media.save()

    return question


def import_question_row(batch, row_number, row_data):
    import_row, _created = QuestionImportRow.objects.get_or_create(
        batch=batch,
        row_number=row_number,
        defaults={"raw_data": row_data},
    )
    import_row.raw_data = row_data
    import_row.status = QuestionImportRowStatus.PENDING
    import_row.error_message = ""
    import_row.question = None
    import_row.content_hash = ""
    import_row.save(
        update_fields=[
            "raw_data",
            "status",
            "error_message",
            "question",
            "content_hash",
            "updated_at",
        ]
    )

    try:
        validated_data = validate_import_row(row_data, batch.uploaded_by, batch)
        import_row.content_hash = validated_data["content_hash"]
        diagram_warning = validated_data.get("diagram_warning", "")
        question = create_question_from_import_row(
            batch=batch,
            validated_data=validated_data,
        )
        import_row.question = question
        import_row.status = QuestionImportRowStatus.IMPORTED
        import_row.error_message = diagram_warning
    except DuplicateQuestionError as exc:
        import_row.status = QuestionImportRowStatus.DUPLICATE
        import_row.error_message = str(exc)
        import_row.content_hash = exc.content_hash
    except ValidationError as exc:
        import_row.status = QuestionImportRowStatus.FAILED
        import_row.error_message = validation_error_message(exc)

    import_row.save(
        update_fields=[
            "status",
            "error_message",
            "question",
            "content_hash",
            "updated_at",
        ]
    )
    return import_row


def process_question_import_batch(batch):
    batch.status = QuestionImportBatchStatus.PROCESSING
    batch.error_summary = ""
    batch.save(update_fields=["status", "error_summary", "updated_at"])

    pending_rows = batch.rows.filter(status=QuestionImportRowStatus.PENDING).order_by(
        "row_number"
    )
    if not pending_rows.exists():
        batch.status = QuestionImportBatchStatus.FAILED
        batch.failed_rows = 0
        batch.duplicate_rows = 0
        batch.successful_rows = 0
        batch.error_summary = "No import rows were found."
        batch.processed_at = timezone.now()
        batch.save(
            update_fields=[
                "status",
                "failed_rows",
                "duplicate_rows",
                "successful_rows",
                "error_summary",
                "processed_at",
                "updated_at",
            ]
        )
        return batch

    for row in pending_rows:
        import_question_row(batch, row.row_number, row.raw_data)

    imported_count = batch.rows.filter(status=QuestionImportRowStatus.IMPORTED).count()
    failed_count = batch.rows.filter(status=QuestionImportRowStatus.FAILED).count()
    duplicate_count = batch.rows.filter(status=QuestionImportRowStatus.DUPLICATE).count()
    error_rows = batch.rows.exclude(status=QuestionImportRowStatus.IMPORTED).order_by(
        "row_number"
    )[:5]
    error_summary = "\n".join(
        f"Row {row.row_number}: {row.error_message}" for row in error_rows
    )

    batch.successful_rows = imported_count
    batch.failed_rows = failed_count
    batch.duplicate_rows = duplicate_count
    batch.error_summary = error_summary
    batch.processed_at = timezone.now()
    if failed_count or duplicate_count:
        batch.status = QuestionImportBatchStatus.COMPLETED_WITH_ERRORS
    else:
        batch.status = QuestionImportBatchStatus.COMPLETED
    batch.save(
        update_fields=[
            "successful_rows",
            "failed_rows",
            "duplicate_rows",
            "error_summary",
            "processed_at",
            "status",
            "updated_at",
        ]
    )
    return batch


def can_review_question(question, reviewer):
    if not reviewer or not reviewer.is_authenticated:
        return False

    if reviewer.role == UserRole.PLATFORM_ADMIN or reviewer.is_superuser:
        return True

    return (
        reviewer.role == UserRole.SCHOOL_ADMIN
        and question.school_id is not None
        and question.school_id == reviewer.school_id
    )


@transaction.atomic
def approve_question(question, reviewer):
    if not can_review_question(question, reviewer):
        raise PermissionDenied("You do not have permission to approve this question.")

    question.status = QuestionStatus.APPROVED
    question.reviewed_by = reviewer
    question.reviewed_at = timezone.now()
    question.is_active = True
    question.full_clean()
    validate_persisted_question_options(question)
    question.save(update_fields=["status", "reviewed_by", "reviewed_at", "is_active", "updated_at"])
    return question


@transaction.atomic
def reject_question(question, reviewer):
    if not can_review_question(question, reviewer):
        raise PermissionDenied("You do not have permission to reject this question.")

    question.status = QuestionStatus.REJECTED
    question.reviewed_by = reviewer
    question.reviewed_at = timezone.now()
    question.full_clean()
    question.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
    return question


@transaction.atomic
def archive_question(question, user):
    if not can_review_question(question, user):
        raise PermissionDenied("You do not have permission to archive this question.")

    question.status = QuestionStatus.ARCHIVED
    question.is_active = False
    question.full_clean()
    question.save(update_fields=["status", "is_active", "updated_at"])
    return question


def validate_persisted_question_options(question):
    options = list(question.options.values("label", "text", "is_correct"))
    validate_question_options(options)


def get_approved_questions_for_topic(
    *,
    school,
    subject,
    topic,
    class_level,
    limit=None,
):
    queryset = (
        Question.objects.filter(
            status=QuestionStatus.APPROVED,
            is_active=True,
            subject=subject,
            topic=topic,
            class_level=class_level,
        )
        .filter(school__isnull=True)
        | Question.objects.filter(
            status=QuestionStatus.APPROVED,
            is_active=True,
            school=school,
            subject=subject,
            topic=topic,
            class_level=class_level,
        )
    )
    queryset = queryset.select_related(
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
    ).prefetch_related("options").order_by("-created_at")

    if limit is not None:
        return queryset[:limit]
    return queryset


def import_questions_from_csv(*args, **kwargs):
    raise NotImplementedError("CSV import will be implemented after the core MVP workflow.")
