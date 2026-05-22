from django.contrib import admin

from apps.question_bank.models import Question, QuestionOption, QuestionSource


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    min_num = 4
    max_num = 4
    fields = ["label", "text", "is_correct"]


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
        "created_by",
        "reviewed_by",
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
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
    inlines = [QuestionOptionInline]
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
