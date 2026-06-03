from django.contrib import admin

from apps.academics.models import (
    AcademicImportBatch,
    AcademicImportRow,
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "starts_at", "ends_at", "is_active"]
    list_filter = ["school", "is_active"]
    search_fields = ["name", "school__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "academic_session",
        "school",
        "starts_at",
        "ends_at",
        "is_active",
    ]
    list_filter = ["school", "academic_session", "name", "is_active"]
    search_fields = ["school__name", "academic_session__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "is_active", "created_at"]
    list_filter = ["school", "is_active"]
    search_fields = ["name", "description", "school__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ClassArm)
class ClassArmAdmin(admin.ModelAdmin):
    list_display = ["name", "class_level", "school", "is_active", "created_at"]
    list_filter = ["school", "class_level", "is_active"]
    search_fields = ["name", "description", "class_level__name", "school__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "school",
        "is_jamb_subject",
        "is_active",
        "created_at",
    ]
    list_filter = ["school", "is_jamb_subject", "is_active"]
    search_fields = ["name", "code", "description", "school__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "subject",
        "class_level",
        "school",
        "jamb_relevance_level",
        "is_active",
    ]
    list_filter = [
        "school",
        "subject",
        "class_level",
        "jamb_relevance_level",
        "is_active",
    ]
    search_fields = ["title", "description", "subject__name", "class_level__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TeacherClassSubjectAssignment)
class TeacherClassSubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "teacher",
        "class_arm",
        "subject",
        "school",
        "academic_session",
        "term",
        "is_active",
    ]
    list_filter = [
        "school",
        "class_arm",
        "subject",
        "academic_session",
        "term",
        "is_active",
    ]
    search_fields = [
        "teacher__full_name",
        "teacher__email",
        "class_arm__name",
        "class_arm__class_level__name",
        "subject__name",
        "school__name",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "class_arm",
        "school",
        "academic_session",
        "term",
        "is_active",
    ]
    list_filter = [
        "school",
        "class_arm",
        "academic_session",
        "term",
        "is_active",
    ]
    search_fields = [
        "student__full_name",
        "student__email",
        "class_arm__name",
        "class_arm__class_level__name",
        "school__name",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(LessonLog)
class LessonLogAdmin(admin.ModelAdmin):
    list_display = [
        "teacher",
        "class_arm",
        "subject",
        "topic",
        "school",
        "taught_at",
        "can_generate_assignment",
    ]
    list_filter = [
        "school",
        "teacher",
        "class_arm",
        "subject",
        "topic",
        "academic_session",
        "term",
    ]
    search_fields = [
        "teacher__full_name",
        "teacher__email",
        "class_arm__name",
        "subject__name",
        "topic__title",
        "notes",
        "school__name",
    ]
    readonly_fields = ["can_generate_assignment", "created_at", "updated_at"]


class AcademicImportRowInline(admin.TabularInline):
    model = AcademicImportRow
    extra = 0
    readonly_fields = [
        "row_number",
        "status",
        "raw_data",
        "error_message",
        "warning_message",
        "student_enrollment",
        "teacher_assignment",
        "created_at",
        "updated_at",
    ]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AcademicImportBatch)
class AcademicImportBatchAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "school",
        "import_type",
        "status",
        "total_rows",
        "successful_rows",
        "failed_rows",
        "duplicate_rows",
        "warning_rows",
        "uploaded_by",
        "created_at",
    ]
    list_filter = ["school", "import_type", "status", "created_at"]
    search_fields = [
        "school__name",
        "uploaded_by__email",
        "uploaded_by__full_name",
        "original_filename",
    ]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [AcademicImportRowInline]


@admin.register(AcademicImportRow)
class AcademicImportRowAdmin(admin.ModelAdmin):
    list_display = [
        "batch",
        "row_number",
        "status",
        "student_enrollment",
        "teacher_assignment",
        "created_at",
    ]
    list_filter = ["status", "batch__import_type", "batch__school"]
    search_fields = [
        "error_message",
        "warning_message",
        "student_enrollment__student__email",
        "teacher_assignment__teacher__email",
    ]
    readonly_fields = ["created_at", "updated_at"]
