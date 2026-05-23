from django.contrib import admin

from apps.ai_generation.models import AIQuestionSuggestionRun


@admin.register(AIQuestionSuggestionRun)
class AIQuestionSuggestionRunAdmin(admin.ModelAdmin):
    list_display = [
        "question",
        "requested_by",
        "school",
        "suggestion_type",
        "status",
        "suggested_topic",
        "suggested_difficulty",
        "confidence_score",
        "applied_by",
        "applied_at",
        "created_at",
    ]
    list_filter = [
        "status",
        "suggestion_type",
        "provider",
        "model_name",
        "school",
        "suggested_difficulty",
        "created_at",
        "applied_at",
    ]
    search_fields = [
        "question__question_text",
        "requested_by__full_name",
        "requested_by__email",
        "duplicate_warning",
        "quality_warning",
        "error_message",
    ]
    readonly_fields = ["created_at", "updated_at", "completed_at", "applied_at"]
    autocomplete_fields = [
        "school",
        "requested_by",
        "question",
        "suggested_topic",
        "applied_by",
    ]
