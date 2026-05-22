import django_filters

from apps.question_bank.models import Question


class QuestionFilter(django_filters.FilterSet):
    source_type = django_filters.CharFilter(field_name="source__source_type")

    class Meta:
        model = Question
        fields = [
            "school",
            "subject",
            "topic",
            "class_level",
            "difficulty",
            "status",
            "source",
            "source_type",
            "is_active",
        ]
