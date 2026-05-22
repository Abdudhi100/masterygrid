from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import StudentProfile, TeacherProfile, User


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
