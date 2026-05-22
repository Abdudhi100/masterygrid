import django_filters

from apps.assignments.models import Assignment


class AssignmentFilter(django_filters.FilterSet):
    starts_at = django_filters.DateTimeFromToRangeFilter()
    due_at = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = Assignment
        fields = [
            "school",
            "teacher",
            "class_arm",
            "subject",
            "topic",
            "status",
            "starts_at",
            "due_at",
        ]
