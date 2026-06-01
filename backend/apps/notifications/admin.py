from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "recipient",
        "school",
        "notification_type",
        "priority",
        "status",
        "created_at",
        "read_at",
    ]
    list_filter = [
        "school",
        "status",
        "priority",
        "notification_type",
        "created_at",
    ]
    search_fields = [
        "title",
        "message",
        "recipient__email",
        "recipient__full_name",
        "actor__email",
    ]
    readonly_fields = ["created_at", "updated_at", "read_at"]
