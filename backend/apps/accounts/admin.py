from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import (
    StudentProfile,
    TeacherProfile,
    User,
    UserImportBatch,
    UserImportRow,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = [
        "email",
        "full_name",
        "role",
        "school",
        "is_active",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["role", "school", "is_active", "is_staff", "is_superuser"]
    search_fields = ["email", "full_name", "school__name"]
    ordering = ["email"]
    readonly_fields = ["last_login", "date_joined", "created_at", "updated_at"]
    filter_horizontal = ["groups", "user_permissions"]

    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        (_("Personal info"), {"fields": ["full_name", "role", "school"]}),
        (
            _("Permissions"),
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
        (_("Important dates"), {"fields": ["last_login", "date_joined"]}),
        (_("Audit"), {"fields": ["created_at", "updated_at"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "email",
                    "full_name",
                    "role",
                    "school",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ],
            },
        ),
    ]


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "school", "staff_id", "phone_number", "created_at"]
    list_filter = ["school"]
    search_fields = [
        "user__email",
        "user__full_name",
        "school__name",
        "staff_id",
        "phone_number",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "school",
        "admission_number",
        "guardian_name",
        "guardian_phone",
        "created_at",
    ]
    list_filter = ["school"]
    search_fields = [
        "user__email",
        "user__full_name",
        "school__name",
        "admission_number",
        "guardian_name",
        "guardian_phone",
    ]
    readonly_fields = ["created_at", "updated_at"]


class UserImportRowInline(admin.TabularInline):
    model = UserImportRow
    extra = 0
    readonly_fields = [
        "row_number",
        "status",
        "raw_data",
        "error_message",
        "warning_message",
        "user",
        "created_at",
        "updated_at",
    ]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(UserImportBatch)
class UserImportBatchAdmin(admin.ModelAdmin):
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
    inlines = [UserImportRowInline]


@admin.register(UserImportRow)
class UserImportRowAdmin(admin.ModelAdmin):
    list_display = ["batch", "row_number", "status", "user", "created_at"]
    list_filter = ["status", "batch__import_type", "batch__school"]
    search_fields = [
        "user__email",
        "user__full_name",
        "error_message",
        "warning_message",
    ]
    readonly_fields = ["created_at", "updated_at"]
