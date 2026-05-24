import csv
import hashlib
import io
import posixpath
import re
import zipfile

from django.core.files.base import ContentFile
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
    QuestionImportFileType,
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
PREFLIGHT_REQUIRED_FIELDS = {
    "subject",
    "class_level",
    "topic",
    "difficulty",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
}
BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "y"}
BOOLEAN_FALSE_VALUES = {"0", "false", "no", "n", ""}
ALLOWED_ZIP_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
IGNORED_ZIP_NAMES = {".ds_store", "thumbs.db"}
MAX_ZIP_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ZIP_FILE_COUNT = 500
MAX_ZIP_IMAGE_BYTES = 5 * 1024 * 1024


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


def detect_import_file_type(uploaded_file):
    filename = getattr(uploaded_file, "name", "")
    lower_filename = filename.lower()
    if lower_filename.endswith(".csv"):
        return QuestionImportFileType.CSV
    if lower_filename.endswith(".zip"):
        return QuestionImportFileType.ZIP
    raise ValidationError({"file": "Only CSV and ZIP imports are supported."})


def parse_csv_import_rows(raw_content):
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


def load_csv_import_rows(uploaded_file):
    uploaded_file.seek(0)
    return parse_csv_import_rows(uploaded_file.read())


def read_csv_from_upload(uploaded_file):
    return load_csv_import_rows(uploaded_file)


def is_ignored_zip_member(normalized_path):
    basename = posixpath.basename(normalized_path).casefold()
    return normalized_path.casefold().startswith("__macosx/") or basename in IGNORED_ZIP_NAMES


def normalize_zip_member_path(name):
    if not name or "\x00" in name:
        raise ValidationError({"file": "ZIP contains an invalid file path."})

    normalized = str(name).replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        raise ValidationError({"file": f"Unsafe ZIP path rejected: {name}"})

    normalized = posixpath.normpath(normalized)
    if normalized in {".", ""}:
        return ""

    parts = normalized.split("/")
    if any(part in {"..", ""} for part in parts):
        raise ValidationError({"file": f"Unsafe ZIP path rejected: {name}"})

    return normalized


def get_file_extension(path):
    _root, extension = posixpath.splitext(path)
    return extension.casefold()


def validate_zip_file(uploaded_file):
    upload_size = getattr(uploaded_file, "size", None)
    if upload_size and upload_size > MAX_ZIP_UPLOAD_BYTES:
        raise ValidationError({"file": "ZIP file is too large."})

    uploaded_file.seek(0)
    try:
        zip_file = zipfile.ZipFile(uploaded_file)
    except zipfile.BadZipFile as exc:
        raise ValidationError({"file": "Uploaded file is not a valid ZIP archive."}) from exc

    infos = zip_file.infolist()
    if len(infos) > MAX_ZIP_FILE_COUNT:
        zip_file.close()
        raise ValidationError({"file": "ZIP contains too many files."})

    total_uncompressed = 0
    normalized_infos = []
    csv_paths = []

    try:
        for info in infos:
            normalized_path = normalize_zip_member_path(info.filename)
            if (
                not normalized_path
                or info.is_dir()
                or is_ignored_zip_member(normalized_path)
            ):
                continue

            if info.flag_bits & 0x1:
                raise ValidationError({"file": "Encrypted ZIP entries are not supported."})

            total_uncompressed += info.file_size
            if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
                raise ValidationError({"file": "ZIP uncompressed content is too large."})

            if normalized_path == "questions.csv":
                csv_paths.append(normalized_path)
            elif normalized_path.startswith("diagrams/"):
                extension = get_file_extension(normalized_path)
                if extension not in ALLOWED_ZIP_IMAGE_EXTENSIONS:
                    raise ValidationError(
                        {
                            "file": (
                                "Unsupported diagram image type in ZIP: "
                                f"{normalized_path}"
                            )
                        }
                    )
                if info.file_size > MAX_ZIP_IMAGE_BYTES:
                    raise ValidationError(
                        {"file": f"Diagram image is too large: {normalized_path}"}
                    )
            else:
                raise ValidationError(
                    {"file": f"Unexpected file in ZIP archive: {normalized_path}"}
                )

            normalized_infos.append((normalized_path, info))

        if len(csv_paths) != 1:
            if not csv_paths:
                raise ValidationError(
                    {"file": "ZIP import must include root questions.csv."}
                )
            raise ValidationError(
                {"file": "ZIP import must include only one questions.csv."}
            )
    except ValidationError:
        zip_file.close()
        raise

    return zip_file, normalized_infos


def normalize_diagram_file_name(name):
    value = normalize_question_text(name).replace("\\", "/")
    if not value:
        return ""
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValidationError({"diagram_file_name": "Unsafe diagram file path."})

    normalized = posixpath.normpath(value)
    parts = normalized.split("/")
    if any(part in {"..", ""} for part in parts):
        raise ValidationError({"diagram_file_name": "Unsafe diagram file path."})

    if "/" in normalized and not normalized.startswith("diagrams/"):
        raise ValidationError(
            {
                "diagram_file_name": (
                    "Diagram file name must be a basename or a path under diagrams/."
                )
            }
        )

    extension = get_file_extension(normalized)
    if extension not in ALLOWED_ZIP_IMAGE_EXTENSIONS:
        raise ValidationError(
            {
                "diagram_file_name": (
                    "Diagram file must be .png, .jpg, .jpeg, or .webp."
                )
            }
        )

    return normalized


def build_zip_image_map(zip_file):
    image_map = {
        "by_path": {},
        "by_basename": {},
    }

    for info in zip_file.infolist():
        normalized_path = normalize_zip_member_path(info.filename)
        if (
            not normalized_path
            or info.is_dir()
            or is_ignored_zip_member(normalized_path)
            or normalized_path == "questions.csv"
        ):
            continue
        if not normalized_path.startswith("diagrams/"):
            continue

        image_bytes = zip_file.read(info)
        basename = posixpath.basename(normalized_path)
        image_record = {
            "bytes": image_bytes,
            "path": normalized_path,
            "filename": basename,
        }
        image_map["by_path"][normalized_path.casefold()] = image_record
        image_map["by_basename"].setdefault(basename.casefold(), []).append(image_record)

    return image_map


def get_image_from_zip_map(image_map, diagram_file_name):
    normalized_name = normalize_diagram_file_name(diagram_file_name)
    if not normalized_name:
        return None

    exact_match = image_map.get("by_path", {}).get(normalized_name.casefold())
    if exact_match:
        return exact_match

    basename = posixpath.basename(normalized_name).casefold()
    basename_matches = image_map.get("by_basename", {}).get(basename, [])
    if len(basename_matches) == 1:
        return basename_matches[0]
    if len(basename_matches) > 1:
        raise ValidationError(
            {
                "diagram_file_name": (
                    f"Diagram filename '{diagram_file_name}' is ambiguous; "
                    "use the full diagrams/... path."
                )
            }
        )
    return None


def read_csv_from_zip(uploaded_file):
    zip_file, normalized_infos = validate_zip_file(uploaded_file)
    try:
        csv_info = next(info for path, info in normalized_infos if path == "questions.csv")
        rows = parse_csv_import_rows(zip_file.read(csv_info))
        image_map = build_zip_image_map(zip_file)
    finally:
        zip_file.close()
        uploaded_file.seek(0)

    return rows, image_map


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


def append_issue(issues, *, field, message, code):
    issues.append({"field": field, "message": message, "code": code})


def public_issues(issues):
    return [
        {
            "field": issue["field"],
            "message": issue["message"],
        }
        for issue in issues
    ]


def issue_codes(issues):
    return {issue["code"] for issue in issues}


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


def analyze_import_row(
    *,
    row_number,
    row_data,
    school,
    source=None,
    file_type=QuestionImportFileType.CSV,
    zip_image_map=None,
):
    errors = []
    warnings = []
    resolved = {
        "subject_id": None,
        "subject_name": "",
        "class_level_id": None,
        "class_level_name": "",
        "topic_id": None,
        "topic_title": "",
    }
    summary_values = {
        "missing_subject": "",
        "missing_class_level": "",
        "missing_topic": "",
        "missing_diagram": "",
        "existing_database_duplicate": False,
    }

    source_required_fields = set()
    if source is None:
        source_required_fields = {"source_name", "source_type"}

    for field in sorted(PREFLIGHT_REQUIRED_FIELDS | source_required_fields):
        if not normalize_question_text(row_data.get(field, "")):
            code = "missing_required_field"
            if field == "correct_option":
                code = "missing_correct_option"
            elif field.startswith("option_"):
                code = "missing_option"
            append_issue(
                errors,
                field=field,
                message=f"{field} is required.",
                code=code,
            )

    subject_name = get_optional_row_value(row_data, "subject")
    class_level_name = get_optional_row_value(row_data, "class_level")
    topic_title = get_optional_row_value(row_data, "topic")
    difficulty = get_optional_row_value(row_data, "difficulty").lower()
    question_text = get_optional_row_value(row_data, "question_text")
    correct_option = get_optional_row_value(row_data, "correct_option").upper()
    diagram_file_name = get_optional_row_value(row_data, "diagram_file_name")

    if difficulty and difficulty not in QuestionDifficulty.values:
        append_issue(
            errors,
            field="difficulty",
            message="Difficulty must be easy, medium, or hard.",
            code="invalid_difficulty",
        )

    if correct_option and correct_option not in QuestionOptionLabel.values:
        append_issue(
            errors,
            field="correct_option",
            message="Correct option must be A, B, C, or D.",
            code="invalid_correct_option",
        )

    try:
        parse_optional_year(row_data.get("year", ""))
    except ValidationError as exc:
        append_issue(
            errors,
            field="year",
            message=validation_error_message(exc),
            code="invalid_year",
        )

    source_type = get_optional_row_value(row_data, "source_type").lower()
    if source is None and source_type and source_type not in QuestionSourceType.values:
        append_issue(
            errors,
            field="source_type",
            message="Source type must be one of the configured source types.",
            code="invalid_source_type",
        )

    has_diagram = False
    needs_manual_review = False
    try:
        has_diagram = parse_optional_bool(
            row_data.get("has_diagram", ""),
            field="has_diagram",
        )
    except ValidationError as exc:
        append_issue(
            errors,
            field="has_diagram",
            message=validation_error_message(exc),
            code="invalid_boolean",
        )

    try:
        needs_manual_review = parse_optional_bool(
            row_data.get("needs_manual_review", ""),
            field="needs_manual_review",
        )
    except ValidationError as exc:
        append_issue(
            errors,
            field="needs_manual_review",
            message=validation_error_message(exc),
            code="invalid_boolean",
        )

    diagram_url = ""
    try:
        diagram_url = validate_external_diagram_url(row_data.get("diagram_url", ""))
    except ValidationError as exc:
        append_issue(
            errors,
            field="diagram_url",
            message=validation_error_message(exc),
            code="invalid_diagram_url",
        )

    normalized_diagram_file_name = ""
    if diagram_file_name:
        try:
            normalized_diagram_file_name = normalize_diagram_file_name(
                diagram_file_name
            )
        except ValidationError as exc:
            append_issue(
                errors,
                field="diagram_file_name",
                message=validation_error_message(exc),
                code="invalid_diagram_file_name",
            )

    subject = None
    if subject_name:
        try:
            subject = find_visible_subject(name=subject_name, school=school)
            resolved["subject_id"] = subject.id
            resolved["subject_name"] = subject.name
        except ValidationError as exc:
            summary_values["missing_subject"] = subject_name
            append_issue(
                errors,
                field="subject",
                message=validation_error_message(exc),
                code="missing_subject",
            )

    class_level = None
    if class_level_name:
        try:
            class_level = find_visible_class_level(name=class_level_name, school=school)
            resolved["class_level_id"] = class_level.id
            resolved["class_level_name"] = class_level.name
        except ValidationError as exc:
            summary_values["missing_class_level"] = class_level_name
            append_issue(
                errors,
                field="class_level",
                message=validation_error_message(exc),
                code="missing_class_level",
            )

    topic = None
    if topic_title and subject and class_level:
        try:
            topic = find_visible_topic(
                title=topic_title,
                subject=subject,
                class_level=class_level,
                school=school,
            )
            resolved["topic_id"] = topic.id
            resolved["topic_title"] = topic.title
        except ValidationError as exc:
            summary_values["missing_topic"] = topic_title
            append_issue(
                errors,
                field="topic",
                message=validation_error_message(exc),
                code="missing_topic",
            )

    options = []
    missing_option_exists = False
    for label in ["A", "B", "C", "D"]:
        field = f"option_{label.lower()}"
        option_text = get_optional_row_value(row_data, field)
        if not option_text:
            missing_option_exists = True
        options.append(
            {
                "label": label,
                "text": option_text,
                "is_correct": label == correct_option,
            }
        )

    option_texts = [
        option["text"].strip().casefold()
        for option in options
        if option["text"].strip()
    ]
    if len(option_texts) != len(set(option_texts)):
        append_issue(
            errors,
            field="options",
            message="Duplicate option text is not allowed for the same question.",
            code="duplicate_option_texts",
        )

    if (
        not missing_option_exists
        and correct_option in QuestionOptionLabel.values
        and not issue_codes(errors).intersection({"duplicate_option_texts"})
    ):
        try:
            validate_question_options(options)
        except ValidationError as exc:
            append_issue(
                errors,
                field="options",
                message=validation_error_message(exc),
                code="invalid_options",
            )

    content_hash = ""
    if (
        question_text
        and subject
        and topic
        and class_level
        and not missing_option_exists
        and correct_option in QuestionOptionLabel.values
        and "duplicate_option_texts" not in issue_codes(errors)
    ):
        content_hash = build_question_content_hash(
            question_text=question_text,
            subject=subject,
            topic=topic,
            class_level=class_level,
            options=options,
        )
        if Question.objects.filter(content_hash=content_hash).exists():
            summary_values["existing_database_duplicate"] = True

    diagram_requested = has_diagram or bool(diagram_url) or bool(diagram_file_name)
    if diagram_url and diagram_file_name and file_type == QuestionImportFileType.ZIP:
        append_issue(
            warnings,
            field="diagram_file_name",
            message=(
                "diagram_url was used and ZIP image will be ignored: "
                f"{diagram_file_name}"
            ),
            code="diagram_url_wins",
        )
    elif normalized_diagram_file_name and file_type == QuestionImportFileType.ZIP:
        try:
            image_record = get_image_from_zip_map(
                zip_image_map or {},
                normalized_diagram_file_name,
            )
            if image_record is None:
                summary_values["missing_diagram"] = diagram_file_name
                append_issue(
                    warnings,
                    field="diagram_file_name",
                    message=f"Diagram file not found in ZIP: {diagram_file_name}",
                    code="missing_diagram",
                )
        except ValidationError as exc:
            append_issue(
                errors,
                field="diagram_file_name",
                message=validation_error_message(exc),
                code="invalid_diagram_file_name",
            )
    elif normalized_diagram_file_name and file_type == QuestionImportFileType.CSV:
        append_issue(
            warnings,
            field="diagram_file_name",
            message=(
                "diagram_file_name is a manual-review hint in CSV imports; "
                "use ZIP import to attach local images."
            ),
            code="manual_diagram_review",
        )
    elif has_diagram and not diagram_url:
        append_issue(
            warnings,
            field="has_diagram",
            message=(
                "Question is marked as having a diagram, but no diagram_url or "
                "diagram_file_name was provided."
            ),
            code="missing_diagram_reference",
        )

    if needs_manual_review and diagram_requested:
        append_issue(
            warnings,
            field="needs_manual_review",
            message="This row is marked for manual review.",
            code="needs_manual_review",
        )

    duplicate_type = ""
    if summary_values["existing_database_duplicate"]:
        duplicate_type = "database"

    return {
        "row_number": row_number,
        "errors": errors,
        "warnings": warnings,
        "duplicate_type": duplicate_type,
        "content_hash": content_hash,
        "question_preview": question_text[:120],
        "subject": subject_name,
        "class_level": class_level_name,
        "topic": topic_title,
        "diagram_file_name": diagram_file_name,
        "resolved": resolved,
        "summary_values": summary_values,
    }


def build_question_import_preflight_report(
    *,
    uploaded_file,
    user,
    school=None,
    source=None,
):
    file_type = detect_import_file_type(uploaded_file)
    zip_image_map = None
    if file_type == QuestionImportFileType.ZIP:
        rows, zip_image_map = read_csv_from_zip(uploaded_file)
    else:
        rows = read_csv_from_upload(uploaded_file)

    summary = {
        "missing_required_fields": 0,
        "missing_correct_option": 0,
        "missing_options": 0,
        "invalid_difficulty": 0,
        "invalid_correct_option": 0,
        "invalid_source_type": 0,
        "duplicate_option_texts": 0,
        "missing_subjects": set(),
        "missing_class_levels": set(),
        "missing_topics": set(),
        "missing_diagrams": 0,
        "duplicate_questions": 0,
        "existing_database_duplicates": 0,
    }
    analyzed_rows = []
    seen_hashes = {}

    for row_number, row_data in rows:
        analysis = analyze_import_row(
            row_number=row_number,
            row_data=row_data,
            school=school,
            source=source,
            file_type=file_type,
            zip_image_map=zip_image_map,
        )

        content_hash = analysis["content_hash"]
        if content_hash:
            if content_hash in seen_hashes and not analysis["duplicate_type"]:
                analysis["duplicate_type"] = "in_file"
            else:
                seen_hashes[content_hash] = row_number

        errors = analysis["errors"]
        warnings = analysis["warnings"]
        error_codes = issue_codes(errors)
        warning_codes = issue_codes(warnings)

        if error_codes.intersection(
            {"missing_required_field", "missing_correct_option", "missing_option"}
        ):
            summary["missing_required_fields"] += 1
        if "missing_correct_option" in error_codes:
            summary["missing_correct_option"] += 1
        if "missing_option" in error_codes:
            summary["missing_options"] += 1
        if "invalid_difficulty" in error_codes:
            summary["invalid_difficulty"] += 1
        if "invalid_correct_option" in error_codes:
            summary["invalid_correct_option"] += 1
        if "invalid_source_type" in error_codes:
            summary["invalid_source_type"] += 1
        if "duplicate_option_texts" in error_codes:
            summary["duplicate_option_texts"] += 1
        if analysis["summary_values"]["missing_subject"]:
            summary["missing_subjects"].add(
                analysis["summary_values"]["missing_subject"]
            )
        if analysis["summary_values"]["missing_class_level"]:
            summary["missing_class_levels"].add(
                analysis["summary_values"]["missing_class_level"]
            )
        if analysis["summary_values"]["missing_topic"]:
            summary["missing_topics"].add(
                analysis["summary_values"]["missing_topic"]
            )
        if "missing_diagram" in warning_codes:
            summary["missing_diagrams"] += 1
        if analysis["duplicate_type"]:
            summary["duplicate_questions"] += 1
        if analysis["duplicate_type"] == "database":
            summary["existing_database_duplicates"] += 1

        if errors:
            status = "invalid"
        elif analysis["duplicate_type"]:
            status = "duplicate"
        elif warnings:
            status = "valid_with_warnings"
        else:
            status = "valid"

        analyzed_rows.append(
            {
                "row_number": analysis["row_number"],
                "status": status,
                "errors": public_issues(errors),
                "warnings": public_issues(warnings),
                "duplicate_type": analysis["duplicate_type"],
                "content_hash": analysis["content_hash"],
                "question_preview": analysis["question_preview"],
                "subject": analysis["subject"],
                "class_level": analysis["class_level"],
                "topic": analysis["topic"],
                "diagram_file_name": analysis["diagram_file_name"],
                "resolved": analysis["resolved"],
            }
        )

    valid_rows = sum(
        1
        for row in analyzed_rows
        if row["status"] in {"valid", "valid_with_warnings"}
    )
    warning_rows = sum(1 for row in analyzed_rows if row["warnings"])
    invalid_rows = sum(1 for row in analyzed_rows if row["status"] == "invalid")
    duplicate_rows = sum(1 for row in analyzed_rows if row["status"] == "duplicate")

    return {
        "file_type": file_type,
        "total_rows": len(analyzed_rows),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "warning_rows": warning_rows,
        "duplicate_rows": duplicate_rows,
        # Duplicates follow the current import behavior: they are counted as
        # duplicate rows, not invalid rows. Warnings also do not block import.
        "can_import": invalid_rows == 0,
        "summary": {
            **summary,
            "missing_subjects": sorted(summary["missing_subjects"]),
            "missing_class_levels": sorted(summary["missing_class_levels"]),
            "missing_topics": sorted(summary["missing_topics"]),
        },
        "rows": analyzed_rows,
    }


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
        if diagram_file_name and batch.file_type == QuestionImportFileType.ZIP:
            diagram_warning = (
                f"Warning: diagram_url was used and ZIP image was ignored: "
                f"{diagram_file_name}"
            )
    elif diagram_file_name:
        if batch.file_type == QuestionImportFileType.ZIP:
            image_record = get_image_from_zip_map(
                getattr(batch, "_zip_image_map", {}),
                diagram_file_name,
            )
            if image_record:
                media.append(
                    {
                        "media_type": QuestionMediaType.IMAGE,
                        "image_bytes": image_record["bytes"],
                        "original_filename": image_record["filename"],
                        "description": diagram_description,
                        "alt_text": diagram_description,
                        "caption": diagram_description[:255],
                        "display_order": 1,
                        "is_primary": True,
                        "is_active": True,
                        "needs_manual_review": needs_manual_review,
                    }
                )
            else:
                needs_manual_review = True
                diagram_warning = (
                    f"Diagram file not found in ZIP: {diagram_file_name}"
                )
        else:
            needs_manual_review = True
            diagram_warning = (
                "Warning: diagram file must be attached manually; CSV file import "
                "does not attach local diagram files."
            )
    elif has_diagram:
        needs_manual_review = True
        diagram_warning = (
            "Warning: question is marked as having a diagram, but no diagram_url "
            "or diagram_file_name was provided."
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


def create_question_media_from_uploaded_image(
    *,
    question,
    image_bytes,
    original_filename,
    media_data,
    user,
):
    media_payload = dict(media_data)
    media_payload.pop("image_bytes", None)
    image_file = ContentFile(image_bytes, name=original_filename)
    media = QuestionMedia(
        question=question,
        created_by=user,
        image=image_file,
        **media_payload,
    )
    media.full_clean()
    media.save()
    return media


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
        image_bytes = media_data.get("image_bytes")
        if image_bytes is not None:
            create_question_media_from_uploaded_image(
                question=question,
                image_bytes=image_bytes,
                original_filename=media_data.get("original_filename", ""),
                media_data=media_data,
                user=batch.uploaded_by,
            )
        else:
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
    import_row.warning_message = ""
    import_row.question = None
    import_row.content_hash = ""
    import_row.save(
        update_fields=[
            "raw_data",
            "status",
            "error_message",
            "warning_message",
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
        import_row.warning_message = diagram_warning
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
            "warning_message",
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
        batch.warning_rows = 0
        batch.successful_rows = 0
        batch.error_summary = "No import rows were found."
        batch.processed_at = timezone.now()
        batch.save(
            update_fields=[
                "status",
                "failed_rows",
                "duplicate_rows",
                "warning_rows",
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
    warning_count = batch.rows.exclude(warning_message="").count()
    error_rows = batch.rows.exclude(status=QuestionImportRowStatus.IMPORTED).order_by(
        "row_number"
    )[:5]
    error_summary = "\n".join(
        f"Row {row.row_number}: {row.error_message}" for row in error_rows
    )

    batch.successful_rows = imported_count
    batch.failed_rows = failed_count
    batch.duplicate_rows = duplicate_count
    batch.warning_rows = warning_count
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
            "warning_rows",
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
