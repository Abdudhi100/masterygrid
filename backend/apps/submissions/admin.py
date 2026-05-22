from django.contrib import admin

from apps.submissions.models import StudentAnswer, Submission


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    fields = [
        "assignment_question",
        "selected_option",
        "is_correct",
        "marks_awarded",
        "answered_at",
    ]
    readonly_fields = ["is_correct", "marks_awarded", "answered_at"]
    autocomplete_fields = ["assignment_question", "selected_option"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "assignment",
        "student",
        "school",
        "status",
        "score",
        "total_marks",
        "percentage",
        "started_at",
        "submitted_at",
        "graded_at",
    ]
    list_filter = [
        "school",
        "assignment",
        "status",
        "started_at",
        "submitted_at",
        "graded_at",
    ]
    search_fields = [
        "assignment__title",
        "student__full_name",
        "student__email",
        "school__name",
    ]
    readonly_fields = [
        "score",
        "total_marks",
        "percentage",
        "started_at",
        "submitted_at",
        "graded_at",
        "question_order",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = ["school", "assignment", "student"]
    inlines = [StudentAnswerInline]


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = [
        "submission",
        "assignment_question",
        "selected_option",
        "is_correct",
        "marks_awarded",
        "answered_at",
    ]
    list_filter = ["is_correct", "marks_awarded", "answered_at"]
    search_fields = [
        "submission__assignment__title",
        "submission__student__full_name",
        "submission__student__email",
        "assignment_question__question__question_text",
        "selected_option__text",
    ]
    readonly_fields = [
        "is_correct",
        "marks_awarded",
        "answered_at",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = ["submission", "assignment_question", "selected_option"]
