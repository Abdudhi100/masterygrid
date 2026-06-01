from django.contrib import admin

from apps.interventions.models import InterventionNote, StudentIntervention


class InterventionNoteInline(admin.TabularInline):
    model = InterventionNote
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(StudentIntervention)
class StudentInterventionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "student",
        "school",
        "category",
        "priority",
        "status",
        "assigned_to",
        "due_date",
        "completed_at",
        "created_at",
    ]
    list_filter = ["school", "category", "priority", "status", "source_type"]
    search_fields = [
        "title",
        "description",
        "student__full_name",
        "student__email",
        "created_by__email",
        "assigned_to__email",
    ]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    inlines = [InterventionNoteInline]


@admin.register(InterventionNote)
class InterventionNoteAdmin(admin.ModelAdmin):
    list_display = ["intervention", "author", "is_internal", "created_at"]
    list_filter = ["is_internal", "created_at"]
    search_fields = ["note", "intervention__title", "author__email"]
    readonly_fields = ["created_at", "updated_at"]
