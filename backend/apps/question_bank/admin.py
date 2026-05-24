from django.contrib import admin

from apps.question_bank.models import (
    Question,
    QuestionImportBatch,
    QuestionImportRow,
    QuestionMedia,
    QuestionOption,
    QuestionSource,
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    min_num = 4
    max_num = 4
    fields = ["label", "text", "is_correct"]


class QuestionMediaInline(admin.TabularInline):
    model = QuestionMedia
    extra = 0
    fields = [
        "media_type",
        "image",
        "external_url",
        "description",
        "caption",
        "display_order",
        "is_primary",
        "is_active",
        "needs_manual_review",
    ]


@admin.register(QuestionSource)
class QuestionSourceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "source_type",
        "exam_body",
        "year",
        "is_active",
        "created_at",
    ]
    list_filter = ["source_type", "exam_body", "year", "is_active"]
    search_fields = ["name", "exam_body", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "short_question_text",
        "school",
        "subject",
        "topic",
        "class_level",
        "difficulty",
        "status",
        "is_active",
        "has_diagram",
        "needs_manual_review",
        "created_by",
        "reviewed_by",
        "content_hash",
    ]
    list_filter = [
        "school",
        "subject",
        "topic",
        "class_level",
        "difficulty",
        "status",
        "source",
        "is_active",
        "has_diagram",
        "needs_manual_review",
    ]
    search_fields = [
        "question_text",
        "explanation",
        "subject__name",
        "topic__title",
        "created_by__full_name",
        "created_by__email",
        "reviewed_by__full_name",
        "reviewed_by__email",
    ]
    readonly_fields = ["created_at", "updated_at", "reviewed_at", "content_hash"]
    inlines = [QuestionOptionInline, QuestionMediaInline]
    autocomplete_fields = [
        "school",
        "subject",
        "topic",
        "class_level",
        "source",
        "created_by",
        "reviewed_by",
    ]

    @admin.display(description="Question")
    def short_question_text(self, obj):
        return obj.question_text[:80]


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ["question", "label", "short_text", "is_correct", "created_at"]
    list_filter = ["label", "is_correct"]
    search_fields = ["text", "question__question_text"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["question"]

    @admin.display(description="Option text")
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(QuestionMedia)
class QuestionMediaAdmin(admin.ModelAdmin):
    list_display = [
        "question",
        "media_type",
        "external_url",
        "original_filename",
        "is_primary",
        "is_active",
        "needs_manual_review",
        "created_at",
    ]
    list_filter = ["media_type", "is_primary", "is_active", "needs_manual_review"]
    search_fields = [
        "question__question_text",
        "external_url",
        "original_filename",
        "description",
        "caption",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["question", "created_by"]


@admin.register(QuestionImportBatch)
class QuestionImportBatchAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "uploaded_by",
        "school",
        "status",
        "total_rows",
        "successful_rows",
        "failed_rows",
        "duplicate_rows",
        "warning_rows",
        "created_at",
        "processed_at",
    ]
    list_filter = ["status", "file_type", "school", "created_at", "processed_at"]
    search_fields = [
        "title",
        "original_filename",
        "uploaded_by__full_name",
        "uploaded_by__email",
        "school__name",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "processed_at",
        "total_rows",
        "successful_rows",
        "failed_rows",
        "duplicate_rows",
        "warning_rows",
        "error_summary",
    ]
    autocomplete_fields = ["school", "uploaded_by", "source"]


@admin.register(QuestionImportRow)
class QuestionImportRowAdmin(admin.ModelAdmin):
    list_display = [
        "batch",
        "row_number",
        "status",
        "short_error_message",
        "short_warning_message",
        "question",
        "content_hash",
        "created_at",
    ]
    list_filter = ["status", "batch", "created_at"]
    search_fields = [
        "batch__title",
        "error_message",
        "content_hash",
        "question__question_text",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "raw_data",
        "error_message",
        "warning_message",
        "content_hash",
    ]
    autocomplete_fields = ["batch", "question"]

    @admin.display(description="Error")
    def short_error_message(self, obj):
        return obj.error_message[:80]

    @admin.display(description="Warning")
    def short_warning_message(self, obj):
        return obj.warning_message[:80]
