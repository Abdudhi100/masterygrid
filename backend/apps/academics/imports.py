import csv
import io

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.academics.models import (
    AcademicImportBatch,
    AcademicImportBatchStatus,
    AcademicImportRow,
    AcademicImportRowStatus,
    AcademicImportType,
    AcademicSession,
    ClassArm,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
)
from apps.accounts.models import StudentProfile, TeacherProfile
from apps.common.choices import UserRole

User = get_user_model()

ENROLLMENT_REQUIRED_COLUMNS = {"academic_session", "term", "class_arm"}
TEACHER_ASSIGNMENT_REQUIRED_COLUMNS = {
    "class_arm",
    "subject",
    "academic_session",
    "term",
}


def normalize_header(value):
    return " ".join(str(value or "").strip().split()).casefold().replace(" ", "_")


def normalize_value(value):
    return " ".join(str(value or "").strip().split())


def parse_csv_upload(uploaded_file):
    uploaded_file.seek(0)
    raw_content = uploaded_file.read()
    uploaded_file.seek(0)
    text_content = raw_content if isinstance(raw_content, str) else raw_content.decode("utf-8-sig")
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
    if import_type == AcademicImportType.STUDENT_ENROLLMENTS:
        return ENROLLMENT_REQUIRED_COLUMNS
    if import_type == AcademicImportType.TEACHER_ASSIGNMENTS:
        return TEACHER_ASSIGNMENT_REQUIRED_COLUMNS
    raise ValidationError({"import_type": "Unsupported academic import type."})


def issue(field, message):
    return {"field": field, "message": message}


def message_from_issues(issues):
    return " ".join(f"{item['field']}: {item['message']}" for item in issues)


def label_matches(obj, value, labels):
    folded = normalize_value(value).casefold()
    return folded in {normalize_value(label).casefold() for label in labels if label}


def find_class_arm(*, school, value):
    value = normalize_value(value)
    if not value:
        return None
    if value.isdigit():
        match = ClassArm.objects.filter(id=int(value), school=school, is_active=True).first()
        if match:
            return match
    for arm in ClassArm.objects.filter(school=school, is_active=True).select_related(
        "class_level"
    ):
        if label_matches(
            arm,
            value,
            [arm.name, str(arm), f"{arm.class_level.name} {arm.name}"],
        ):
            return arm
    return None


def find_academic_session(*, school, value):
    value = normalize_value(value)
    if not value:
        return None
    queryset = AcademicSession.objects.filter(school=school)
    if value.isdigit():
        match = queryset.filter(id=int(value)).first()
        if match:
            return match
    return queryset.filter(name__iexact=value).first()


def find_term(*, school, academic_session, value):
    value = normalize_value(value)
    if not value:
        return None
    queryset = Term.objects.filter(school=school, academic_session=academic_session)
    if value.isdigit():
        match = queryset.filter(id=int(value)).first()
        if match:
            return match
    for term in queryset:
        if label_matches(term, value, [term.name, term.get_name_display(), str(term)]):
            return term
    return None


def find_subject(*, school, value):
    value = normalize_value(value)
    if not value:
        return None
    queryset = Subject.objects.filter(is_active=True).filter(
        Q(school__isnull=True) | Q(school=school)
    )
    if value.isdigit():
        match = queryset.filter(id=int(value)).first()
        if match:
            return match
    return queryset.filter(Q(name__iexact=value) | Q(code__iexact=value)).order_by(
        "-school_id"
    ).first()


def find_student(*, school, row_data):
    email = normalize_value(row_data.get("student_email", "")).casefold()
    admission_number = normalize_value(row_data.get("admission_number", ""))
    if email:
        return User.objects.filter(
            role=UserRole.STUDENT,
            school=school,
            email__iexact=email,
            is_active=True,
        ).first()
    if admission_number:
        profile = StudentProfile.objects.select_related("user").filter(
            school=school,
            admission_number__iexact=admission_number,
            user__is_active=True,
        ).first()
        return profile.user if profile else None
    return None


def find_teacher(*, school, row_data):
    email = normalize_value(row_data.get("teacher_email", "")).casefold()
    staff_id = normalize_value(row_data.get("staff_id", ""))
    if email:
        return User.objects.filter(
            role=UserRole.TEACHER,
            school=school,
            email__iexact=email,
            is_active=True,
        ).first()
    if staff_id:
        profile = TeacherProfile.objects.select_related("user").filter(
            school=school,
            staff_id__iexact=staff_id,
            user__is_active=True,
        ).first()
        return profile.user if profile else None
    return None


def analyze_academic_import_rows(*, rows, import_type, school):
    analyzed_rows = []
    seen_keys = {}
    summary = {
        "missing_required_fields": 0,
        "missing_students": 0,
        "missing_teachers": 0,
        "missing_class_arms": set(),
        "missing_subjects": set(),
        "missing_academic_sessions": set(),
        "missing_terms": set(),
        "duplicate_rows": 0,
        "existing_records": 0,
    }

    for row_number, row_data in rows:
        errors = []
        warnings = []
        duplicate_type = ""
        required_columns = required_columns_for_import_type(import_type)

        for field in sorted(required_columns):
            if not normalize_value(row_data.get(field, "")):
                errors.append(issue(field, f"{field} is required."))
        if errors:
            summary["missing_required_fields"] += 1

        academic_session = find_academic_session(
            school=school,
            value=row_data.get("academic_session", ""),
        )
        if normalize_value(row_data.get("academic_session", "")) and not academic_session:
            summary["missing_academic_sessions"].add(
                normalize_value(row_data.get("academic_session", ""))
            )
            errors.append(issue("academic_session", "Academic session was not found."))

        term = None
        if academic_session:
            term = find_term(school=school, academic_session=academic_session, value=row_data.get("term", ""))
        if normalize_value(row_data.get("term", "")) and not term:
            summary["missing_terms"].add(normalize_value(row_data.get("term", "")))
            errors.append(issue("term", "Term was not found for the selected session."))

        class_arm = find_class_arm(school=school, value=row_data.get("class_arm", ""))
        if normalize_value(row_data.get("class_arm", "")) and not class_arm:
            summary["missing_class_arms"].add(normalize_value(row_data.get("class_arm", "")))
            errors.append(issue("class_arm", "Class arm was not found."))

        subject = None
        student = None
        teacher = None
        if import_type == AcademicImportType.TEACHER_ASSIGNMENTS:
            subject = find_subject(school=school, value=row_data.get("subject", ""))
            if normalize_value(row_data.get("subject", "")) and not subject:
                summary["missing_subjects"].add(normalize_value(row_data.get("subject", "")))
                errors.append(issue("subject", "Subject was not found."))

        if import_type == AcademicImportType.STUDENT_ENROLLMENTS:
            student_lookup_present = normalize_value(row_data.get("student_email", "")) or normalize_value(
                row_data.get("admission_number", "")
            )
            if not student_lookup_present:
                errors.append(issue("student", "student_email or admission_number is required."))
                summary["missing_required_fields"] += 1
            student = find_student(school=school, row_data=row_data)
            if student_lookup_present and not student:
                summary["missing_students"] += 1
                errors.append(issue("student", "Student was not found."))

            record_key = (
                student.id if student else "",
                academic_session.id if academic_session else "",
                term.id if term else "",
            )
            if all(record_key):
                if record_key in seen_keys:
                    duplicate_type = "in_file"
                    warnings.append(
                        issue("row", f"Duplicate enrollment in file; first seen on row {seen_keys[record_key]}.")
                    )
                    summary["duplicate_rows"] += 1
                else:
                    seen_keys[record_key] = row_number
                if StudentEnrollment.objects.filter(
                    student=student,
                    academic_session=academic_session,
                    term=term,
                ).exists():
                    duplicate_type = "database"
                    warnings.append(issue("row", "Enrollment already exists."))
                    summary["existing_records"] += 1
        else:
            teacher_lookup_present = normalize_value(row_data.get("teacher_email", "")) or normalize_value(
                row_data.get("staff_id", "")
            )
            if not teacher_lookup_present:
                errors.append(issue("teacher", "teacher_email or staff_id is required."))
                summary["missing_required_fields"] += 1
            teacher = find_teacher(school=school, row_data=row_data)
            if teacher_lookup_present and not teacher:
                summary["missing_teachers"] += 1
                errors.append(issue("teacher", "Teacher was not found."))

            record_key = (
                teacher.id if teacher else "",
                class_arm.id if class_arm else "",
                subject.id if subject else "",
                academic_session.id if academic_session else "",
                term.id if term else "",
            )
            if all(record_key):
                if record_key in seen_keys:
                    duplicate_type = "in_file"
                    warnings.append(
                        issue("row", f"Duplicate teacher assignment in file; first seen on row {seen_keys[record_key]}.")
                    )
                    summary["duplicate_rows"] += 1
                else:
                    seen_keys[record_key] = row_number
                if TeacherClassSubjectAssignment.objects.filter(
                    teacher=teacher,
                    class_arm=class_arm,
                    subject=subject,
                    academic_session=academic_session,
                    term=term,
                ).exists():
                    duplicate_type = "database"
                    warnings.append(issue("row", "Teacher assignment already exists."))
                    summary["existing_records"] += 1

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
                "raw_data": row_data,
                "student": normalize_value(row_data.get("student_email", ""))
                or normalize_value(row_data.get("admission_number", "")),
                "teacher": normalize_value(row_data.get("teacher_email", ""))
                or normalize_value(row_data.get("staff_id", "")),
                "class_arm": normalize_value(row_data.get("class_arm", "")),
                "subject": normalize_value(row_data.get("subject", "")),
                "academic_session": normalize_value(row_data.get("academic_session", "")),
                "term": normalize_value(row_data.get("term", "")),
                "resolved": {
                    "student_id": student.id if student else None,
                    "student_name": student.full_name if student else "",
                    "teacher_id": teacher.id if teacher else None,
                    "teacher_name": teacher.full_name if teacher else "",
                    "class_arm_id": class_arm.id if class_arm else None,
                    "class_arm_name": str(class_arm) if class_arm else "",
                    "subject_id": subject.id if subject else None,
                    "subject_name": subject.name if subject else "",
                    "academic_session_id": academic_session.id if academic_session else None,
                    "academic_session_name": academic_session.name if academic_session else "",
                    "term_id": term.id if term else None,
                    "term_name": term.get_name_display() if term else "",
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
            "missing_subjects": sorted(summary["missing_subjects"]),
            "missing_academic_sessions": sorted(summary["missing_academic_sessions"]),
            "missing_terms": sorted(summary["missing_terms"]),
        },
        "rows": analyzed_rows,
    }


def build_academic_import_preflight_report(*, uploaded_file, import_type, school):
    validate_csv_file(uploaded_file)
    rows, fieldnames = parse_csv_upload(uploaded_file)
    missing_columns = sorted(required_columns_for_import_type(import_type) - fieldnames)
    if missing_columns:
        raise ValidationError(
            {"file": f"CSV is missing required column(s): {', '.join(missing_columns)}."}
        )

    report = analyze_academic_import_rows(rows=rows, import_type=import_type, school=school)
    return {"import_type": import_type, "file_type": "csv", **report}


@transaction.atomic
def create_academic_record(*, import_type, school, row_data):
    academic_session = find_academic_session(
        school=school,
        value=row_data.get("academic_session", ""),
    )
    term = find_term(
        school=school,
        academic_session=academic_session,
        value=row_data.get("term", ""),
    )
    class_arm = find_class_arm(school=school, value=row_data.get("class_arm", ""))

    if import_type == AcademicImportType.STUDENT_ENROLLMENTS:
        student = find_student(school=school, row_data=row_data)
        enrollment = StudentEnrollment(
            school=school,
            student=student,
            class_arm=class_arm,
            academic_session=academic_session,
            term=term,
            is_active=True,
        )
        enrollment.full_clean()
        enrollment.save()
        return enrollment, None

    teacher = find_teacher(school=school, row_data=row_data)
    subject = find_subject(school=school, value=row_data.get("subject", ""))
    assignment = TeacherClassSubjectAssignment(
        school=school,
        teacher=teacher,
        class_arm=class_arm,
        subject=subject,
        academic_session=academic_session,
        term=term,
        is_active=True,
    )
    assignment.full_clean()
    assignment.save()
    return None, assignment


def process_academic_import(*, uploaded_file, import_type, school, uploaded_by):
    validate_csv_file(uploaded_file)
    rows, fieldnames = parse_csv_upload(uploaded_file)
    missing_columns = sorted(required_columns_for_import_type(import_type) - fieldnames)
    if missing_columns:
        raise ValidationError(
            {"file": f"CSV is missing required column(s): {', '.join(missing_columns)}."}
        )

    batch = AcademicImportBatch.objects.create(
        school=school,
        uploaded_by=uploaded_by,
        import_type=import_type,
        file=uploaded_file,
        original_filename=getattr(uploaded_file, "name", ""),
        status=AcademicImportBatchStatus.PROCESSING,
    )
    report = analyze_academic_import_rows(rows=rows, import_type=import_type, school=school)
    batch.total_rows = report["total_rows"]
    batch.save(update_fields=["total_rows", "updated_at"])

    for analyzed_row in report["rows"]:
        row = AcademicImportRow.objects.create(
            batch=batch,
            row_number=analyzed_row["row_number"],
            raw_data=analyzed_row["raw_data"],
        )
        if analyzed_row["status"] == "invalid":
            row.status = AcademicImportRowStatus.FAILED
            row.error_message = message_from_issues(analyzed_row["errors"])
        elif analyzed_row["status"] == "duplicate":
            row.status = AcademicImportRowStatus.DUPLICATE
            row.warning_message = message_from_issues(analyzed_row["warnings"])
        else:
            try:
                enrollment, assignment = create_academic_record(
                    import_type=import_type,
                    school=school,
                    row_data=analyzed_row["raw_data"],
                )
                row.student_enrollment = enrollment
                row.teacher_assignment = assignment
                row.status = (
                    AcademicImportRowStatus.WARNING
                    if analyzed_row["warnings"]
                    else AcademicImportRowStatus.IMPORTED
                )
                row.warning_message = message_from_issues(analyzed_row["warnings"])
            except Exception as exc:
                row.status = AcademicImportRowStatus.FAILED
                row.error_message = str(exc)

        row.save(
            update_fields=[
                "status",
                "error_message",
                "warning_message",
                "student_enrollment",
                "teacher_assignment",
                "updated_at",
            ]
        )

    batch.successful_rows = batch.rows.filter(
        status__in=[AcademicImportRowStatus.IMPORTED, AcademicImportRowStatus.WARNING]
    ).count()
    batch.failed_rows = batch.rows.filter(status=AcademicImportRowStatus.FAILED).count()
    batch.duplicate_rows = batch.rows.filter(status=AcademicImportRowStatus.DUPLICATE).count()
    batch.warning_rows = batch.rows.exclude(warning_message="").count()
    batch.status = (
        AcademicImportBatchStatus.COMPLETED_WITH_ERRORS
        if batch.failed_rows or batch.duplicate_rows
        else AcademicImportBatchStatus.COMPLETED
    )
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
