from django.contrib import admin

from apps.schools.models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "email", "phone", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug", "email", "phone"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]
