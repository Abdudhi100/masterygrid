from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "category",
        "action",
        "actor_email",
        "school",
        "object_type",
        "object_id",
        "target_user_email",
    ]
    list_filter = ["category", "action", "school", "actor_role", "created_at"]
    search_fields = [
        "actor_email",
        "target_user_email",
        "action",
        "object_type",
        "object_id",
        "object_repr",
    ]
    readonly_fields = [
        "school",
        "actor",
        "actor_email",
        "actor_role",
        "action",
        "category",
        "object_type",
        "object_id",
        "object_repr",
        "target_user",
        "target_user_email",
        "ip_address",
        "user_agent",
        "metadata",
        "created_at",
    ]
