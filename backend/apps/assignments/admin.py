from django.contrib import admin

from apps.assignments.models import Assignment, AssignmentQuestion


class AssignmentQuestionInline(admin.TabularInline):
    model = AssignmentQuestion
    extra = 0
    fields = ["question", "order", "marks"]
    autocomplete_fields = ["question"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "school",
        "teacher",
        "class_arm",
        "subject",
        "topic",
        "question_count",
        "status",
        "published_at",
        "due_at",
        "allow_late_submissions",
        "late_submission_deadline",
    ]
    list_filter = [
        "school",
        "teacher",
        "class_arm",
        "subject",
        "topic",
        "status",
        "starts_at",
        "due_at",
        "allow_late_submissions",
        "late_submission_deadline",
    ]
    search_fields = [
        "title",
        "instructions",
        "teacher__full_name",
        "teacher__email",
        "class_arm__name",
        "subject__name",
        "topic__title",
        "school__name",
    ]
    readonly_fields = [
        "published_at",
        "original_due_at",
        "deadline_extended_at",
        "deadline_extended_by",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = [
        "school",
        "teacher",
        "class_arm",
        "subject",
        "topic",
        "lesson_log",
    ]
    inlines = [AssignmentQuestionInline]


@admin.register(AssignmentQuestion)
class AssignmentQuestionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "question", "order", "marks", "created_at"]
    list_filter = ["assignment__school", "assignment", "marks"]
    search_fields = ["assignment__title", "question__question_text"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["assignment", "question"]
