import csv
import io
import secrets

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from apps.accounts.models import (
    StudentProfile,
    TeacherProfile,
    UserImportBatch,
    UserImportBatchStatus,
    UserImportRow,
    UserImportRowStatus,
    UserImportType,
)
from apps.academics.models import ClassArm
from apps.common.choices import UserRole

User = get_user_model()

STUDENT_REQUIRED_COLUMNS = {"full_name", "email", "admission_number", "class_arm"}
TEACHER_REQUIRED_COLUMNS = {"full_name", "email", "staff_id"}
COMMON_OPTIONAL_COLUMNS = {"password", "phone_number", "guardian_name", "guardian_phone"}


def normalize_header(value):
    return " ".join(str(value or "").strip().split()).casefold().replace(" ", "_")


def normalize_value(value):
    return " ".join(str(value or "").strip().split())


def parse_csv_upload(uploaded_file):
    uploaded_file.seek(0)
    raw_content = uploaded_file.read()
    uploaded_file.seek(0)
    if isinstance(raw_content, str):
        text_content = raw_content
    else:
        text_content = raw_content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text_content))
    if not reader.fieldnames:
        raise ValidationError({"file": "CSV file must include a header row."})

    rows = []
    for line_number, row in enumerate(reader, start=2):
        normalized_row = {
            normalize_header(key): "" if value is None else str(value).strip()
            for key, value in row.items()
            if key is not None
        }
        if any(value for value in normalized_row.values()):
            rows.append((line_number, normalized_row))
    return rows, {normalize_header(field) for field in reader.fieldnames if field}


def validate_csv_file(uploaded_file):
    filename = getattr(uploaded_file, "name", "")
    if not filename.lower().endswith(".csv"):
        raise ValidationError({"file": "Only CSV imports are supported."})
    return uploaded_file


def required_columns_for_import_type(import_type):
    if import_type == UserImportType.STUDENTS:
        return STUDENT_REQUIRED_COLUMNS
    if import_type == UserImportType.TEACHERS:
        return TEACHER_REQUIRED_COLUMNS
    raise ValidationError({"import_type": "Unsupported user import type."})


def issue(field, message):
    return {"field": field, "message": message}


def message_from_issues(issues):
    return " ".join(f"{item['field']}: {item['message']}" for item in issues)


def find_class_arm_by_label(*, school, label):
    value = normalize_value(label)
    if not value:
        return None

    if value.isdigit():
        arm = ClassArm.objects.filter(id=int(value), school=school, is_active=True).first()
        if arm:
            return arm

    arms = ClassArm.objects.filter(school=school, is_active=True).select_related(
        "class_level"
    )
    folded = value.casefold()
    for arm in arms:
        candidates = {
            arm.name,
            str(arm),
            f"{arm.class_level.name} {arm.name}",
        }
        if folded in {candidate.casefold() for candidate in candidates}:
            return arm
    return None


def validate_password(value):
    password = str(value or "")
    if password and len(password) < 8:
        raise ValidationError("Password must be at least 8 characters.")
    return password


def analyze_user_import_rows(*, rows, import_type, school):
    required_columns = required_columns_for_import_type(import_type)
    seen_emails = {}
    seen_identifiers = {}
    analyzed_rows = []
    summary = {
        "missing_required_fields": 0,
        "invalid_emails": 0,
        "duplicate_emails": 0,
        "existing_emails": 0,
        "duplicate_identifiers": 0,
        "existing_identifiers": 0,
        "missing_class_arms": set(),
    }

    for row_number, row_data in rows:
        errors = []
        warnings = []
        duplicate_type = ""
        full_name = normalize_value(row_data.get("full_name", ""))
        email = normalize_value(row_data.get("email", "")).casefold()
        identifier_field = (
            "admission_number"
            if import_type == UserImportType.STUDENTS
            else "staff_id"
        )
        identifier = normalize_value(row_data.get(identifier_field, ""))
        class_arm_label = normalize_value(row_data.get("class_arm", ""))
        class_arm = None

        for field in sorted(required_columns):
            if not normalize_value(row_data.get(field, "")):
                errors.append(issue(field, f"{field} is required."))

        if errors:
            summary["missing_required_fields"] += 1

        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors.append(issue("email", "Enter a valid email address."))
                summary["invalid_emails"] += 1

            if email in seen_emails:
                duplicate_type = "in_file"
                summary["duplicate_emails"] += 1
                warnings.append(
                    issue(
                        "email",
                        f"Duplicate email in file; first seen on row {seen_emails[email]}.",
                    )
                )
            else:
                seen_emails[email] = row_number

            if User.objects.filter(email__iexact=email).exists():
                duplicate_type = "database"
                summary["existing_emails"] += 1
                warnings.append(issue("email", "A user with this email already exists."))

        identifier_key = identifier.casefold()
        if identifier_key:
            if identifier_key in seen_identifiers:
                duplicate_type = "in_file"
                summary["duplicate_identifiers"] += 1
                warnings.append(
                    issue(
                        identifier_field,
                        (
                            f"Duplicate {identifier_field} in file; first seen on row "
                            f"{seen_identifiers[identifier_key]}."
                        ),
                    )
                )
            else:
                seen_identifiers[identifier_key] = row_number

            if import_type == UserImportType.STUDENTS:
                exists = StudentProfile.objects.filter(
                    school=school,
                    admission_number__iexact=identifier,
                ).exists()
            else:
                exists = TeacherProfile.objects.filter(
                    school=school,
                    staff_id__iexact=identifier,
                ).exists()
            if exists:
                duplicate_type = "database"
                summary["existing_identifiers"] += 1
                warnings.append(
                    issue(identifier_field, "This identifier already exists in school.")
                )

        if import_type == UserImportType.STUDENTS and class_arm_label:
            class_arm = find_class_arm_by_label(school=school, label=class_arm_label)
            if class_arm is None:
                errors.append(issue("class_arm", f"Class arm '{class_arm_label}' was not found."))
                summary["missing_class_arms"].add(class_arm_label)

        try:
            validate_password(row_data.get("password", ""))
        except ValidationError as exc:
            errors.append(issue("password", exc.messages[0]))

        if errors:
            status = "invalid"
        elif duplicate_type:
            status = "duplicate"
        elif warnings:
            status = "valid_with_warnings"
        else:
            status = "valid"

        analyzed_rows.append(
            {
                "row_number": row_number,
                "status": status,
                "errors": errors,
                "warnings": warnings,
                "duplicate_type": duplicate_type,
                "full_name": full_name,
                "email": email,
                "identifier": identifier,
                "class_arm": class_arm_label,
                "raw_data": row_data,
                "resolved": {
                    "class_arm_id": class_arm.id if class_arm else None,
                    "class_arm_name": str(class_arm) if class_arm else "",
                },
            }
        )

    valid_rows = sum(
        1 for row in analyzed_rows if row["status"] in {"valid", "valid_with_warnings"}
    )
    invalid_rows = sum(1 for row in analyzed_rows if row["status"] == "invalid")
    duplicate_rows = sum(1 for row in analyzed_rows if row["status"] == "duplicate")
    warning_rows = sum(1 for row in analyzed_rows if row["warnings"])

    return {
        "total_rows": len(analyzed_rows),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "warning_rows": warning_rows,
        "duplicate_rows": duplicate_rows,
        "can_import": invalid_rows == 0,
        "summary": {
            **summary,
            "missing_class_arms": sorted(summary["missing_class_arms"]),
        },
        "rows": analyzed_rows,
    }


def build_user_import_preflight_report(*, uploaded_file, import_type, school):
    validate_csv_file(uploaded_file)
    rows, fieldnames = parse_csv_upload(uploaded_file)
    missing_columns = sorted(required_columns_for_import_type(import_type) - fieldnames)
    if missing_columns:
        raise ValidationError(
            {"file": f"CSV is missing required column(s): {', '.join(missing_columns)}."}
        )

    report = analyze_user_import_rows(rows=rows, import_type=import_type, school=school)
    return {
        "import_type": import_type,
        "file_type": "csv",
        **report,
    }


@transaction.atomic
def create_imported_user(*, import_type, school, row_data):
    full_name = normalize_value(row_data.get("full_name", ""))
    email = normalize_value(row_data.get("email", "")).casefold()
    password = validate_password(row_data.get("password", "")) or secrets.token_urlsafe(12)

    role = UserRole.STUDENT if import_type == UserImportType.STUDENTS else UserRole.TEACHER
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=role,
        school=school,
    )

    if import_type == UserImportType.STUDENTS:
        StudentProfile.objects.create(
            user=user,
            school=school,
            admission_number=normalize_value(row_data.get("admission_number", "")),
            guardian_name=normalize_value(row_data.get("guardian_name", "")),
            guardian_phone=normalize_value(row_data.get("guardian_phone", "")),
        )
    else:
        TeacherProfile.objects.create(
            user=user,
            school=school,
            staff_id=normalize_value(row_data.get("staff_id", "")),
            phone_number=normalize_value(row_data.get("phone_number", "")),
        )

    return user


def process_user_import(*, uploaded_file, import_type, school, uploaded_by):
    validate_csv_file(uploaded_file)
    rows, fieldnames = parse_csv_upload(uploaded_file)
    missing_columns = sorted(required_columns_for_import_type(import_type) - fieldnames)
    if missing_columns:
        raise ValidationError(
            {"file": f"CSV is missing required column(s): {', '.join(missing_columns)}."}
        )

    batch = UserImportBatch.objects.create(
        school=school,
        uploaded_by=uploaded_by,
        import_type=import_type,
        file=uploaded_file,
        original_filename=getattr(uploaded_file, "name", ""),
        status=UserImportBatchStatus.PROCESSING,
    )

    report = analyze_user_import_rows(rows=rows, import_type=import_type, school=school)
    batch.total_rows = report["total_rows"]
    batch.save(update_fields=["total_rows", "updated_at"])

    for analyzed_row in report["rows"]:
        row = UserImportRow.objects.create(
            batch=batch,
            row_number=analyzed_row["row_number"],
            raw_data=analyzed_row["raw_data"],
        )

        if analyzed_row["status"] == "invalid":
            row.status = UserImportRowStatus.FAILED
            row.error_message = message_from_issues(analyzed_row["errors"])
        elif analyzed_row["status"] == "duplicate":
            row.status = UserImportRowStatus.DUPLICATE
            row.warning_message = message_from_issues(analyzed_row["warnings"])
        else:
            try:
                user = create_imported_user(
                    import_type=import_type,
                    school=school,
                    row_data=analyzed_row["raw_data"],
                )
                row.user = user
                if analyzed_row["warnings"]:
                    row.status = UserImportRowStatus.WARNING
                    row.warning_message = message_from_issues(analyzed_row["warnings"])
                else:
                    row.status = UserImportRowStatus.IMPORTED
            except Exception as exc:  # defensive: row failure must not crash full import
                row.status = UserImportRowStatus.FAILED
                row.error_message = str(exc)

        row.save(
            update_fields=[
                "status",
                "error_message",
                "warning_message",
                "user",
                "updated_at",
            ]
        )

    batch.successful_rows = batch.rows.filter(
        status__in=[UserImportRowStatus.IMPORTED, UserImportRowStatus.WARNING]
    ).count()
    batch.failed_rows = batch.rows.filter(status=UserImportRowStatus.FAILED).count()
    batch.duplicate_rows = batch.rows.filter(status=UserImportRowStatus.DUPLICATE).count()
    batch.warning_rows = batch.rows.exclude(warning_message="").count()
    if batch.failed_rows or batch.duplicate_rows:
        batch.status = UserImportBatchStatus.COMPLETED_WITH_ERRORS
    else:
        batch.status = UserImportBatchStatus.COMPLETED
    first_error = batch.rows.exclude(error_message="").order_by("row_number").first()
    batch.error_message = first_error.error_message if first_error else ""
    batch.save(
        update_fields=[
            "successful_rows",
            "failed_rows",
            "duplicate_rows",
            "warning_rows",
            "status",
            "error_message",
            "updated_at",
        ]
    )
    return batch
