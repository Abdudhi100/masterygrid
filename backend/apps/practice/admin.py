from django.contrib import admin

from apps.practice.models import (
    PracticeAnswer,
    PracticeSession,
    PracticeSessionQuestion,
)


class PracticeSessionQuestionInline(admin.TabularInline):
    model = PracticeSessionQuestion
    extra = 0
    readonly_fields = [
        "question",
        "order",
        "marks",
        "question_text",
        "explanation",
        "options_snapshot",
    ]


class PracticeAnswerInline(admin.TabularInline):
    model = PracticeAnswer
    extra = 0
    readonly_fields = [
        "session_question",
        "selected_option",
        "selected_label",
        "is_correct",
        "marks_awarded",
        "answered_at",
    ]


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "school",
        "subject",
        "topic",
        "difficulty",
        "status",
        "score",
        "total_marks",
        "percentage",
        "started_at",
        "submitted_at",
    ]
    list_filter = [
        "status",
        "difficulty",
        "school",
        "subject",
        "topic",
        "started_at",
        "submitted_at",
    ]
    search_fields = [
        "student__full_name",
        "student__email",
        "subject__name",
        "topic__title",
    ]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [PracticeSessionQuestionInline, PracticeAnswerInline]


@admin.register(PracticeSessionQuestion)
class PracticeSessionQuestionAdmin(admin.ModelAdmin):
    list_display = [
        "session",
        "question",
        "order",
        "marks",
        "created_at",
    ]
    list_filter = ["session__school", "session__subject", "session__status"]
    search_fields = ["question_text", "question__question_text"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(PracticeAnswer)
class PracticeAnswerAdmin(admin.ModelAdmin):
    list_display = [
        "session",
        "session_question",
        "selected_label",
        "is_correct",
        "marks_awarded",
        "answered_at",
    ]
    list_filter = ["is_correct", "session__school", "session__subject"]
    search_fields = ["session__student__full_name", "session__student__email"]
    readonly_fields = ["created_at", "updated_at"]
