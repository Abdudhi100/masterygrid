import django_filters

from apps.submissions.models import Submission


class SubmissionFilter(django_filters.FilterSet):
    submitted_at = django_filters.DateTimeFromToRangeFilter()
    graded_at = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = Submission
        fields = [
            "assignment",
            "student",
            "status",
            "school",
            "submitted_at",
            "graded_at",
        ]
