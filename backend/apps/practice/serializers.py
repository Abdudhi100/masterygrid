from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.academics.models import ClassLevel, Subject, Topic
from apps.practice.models import (
    PracticeAnswer,
    PracticeDifficulty,
    PracticeSession,
    PracticeSessionQuestion,
)
from apps.practice.services import (
    get_practice_result,
    start_practice_session,
    submit_practice_session,
)
from apps.question_bank.models import QuestionOption
from apps.question_bank.serializers import StudentQuestionMediaSerializer


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    if hasattr(exc, "messages"):
        raise serializers.ValidationError(exc.messages)
    raise serializers.ValidationError(str(exc))


class PracticeStartSerializer(serializers.Serializer):
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.filter(is_active=True),
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    class_level = serializers.PrimaryKeyRelatedField(
        queryset=ClassLevel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    difficulty = serializers.ChoiceField(
        choices=PracticeDifficulty.values,
        default=PracticeDifficulty.MIXED,
    )
    question_count = serializers.IntegerField(min_value=1, max_value=100)

    def create(self, validated_data):
        request = self.context["request"]
        try:
            return start_practice_session(
                student=request.user,
                subject=validated_data["subject"],
                topic=validated_data.get("topic"),
                class_level=validated_data.get("class_level"),
                difficulty=validated_data.get(
                    "difficulty",
                    PracticeDifficulty.MIXED,
                ),
                question_count=validated_data["question_count"],
            )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


class PracticeOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()
    text = serializers.CharField()


class PracticeQuestionSerializer(serializers.ModelSerializer):
    session_question = serializers.IntegerField(source="id")
    has_diagram = serializers.BooleanField(source="question.has_diagram", read_only=True)
    diagram_description = serializers.CharField(
        source="question.diagram_description",
        read_only=True,
    )
    media = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    class Meta:
        model = PracticeSessionQuestion
        fields = [
            "session_question",
            "order",
            "question_text",
            "has_diagram",
            "diagram_description",
            "media",
            "marks",
            "options",
        ]
        read_only_fields = fields

    def get_media(self, obj):
        media = obj.question.media.filter(is_active=True).order_by(
            "-is_primary",
            "display_order",
            "id",
        )
        return StudentQuestionMediaSerializer(
            media,
            many=True,
            context=self.context,
        ).data

    def get_options(self, obj):
        options = [
            {
                "id": option["id"],
                "label": option["label"],
                "text": option["text"],
            }
            for option in obj.options_snapshot
        ]
        return PracticeOptionSerializer(options, many=True).data


class PracticeSessionBaseSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    class_level_name = serializers.CharField(source="class_level.name", read_only=True)
    class_arm_name = serializers.SerializerMethodField()

    class Meta:
        model = PracticeSession
        fields = [
            "id",
            "school",
            "student",
            "subject",
            "subject_name",
            "topic",
            "topic_title",
            "class_level",
            "class_level_name",
            "class_arm",
            "class_arm_name",
            "difficulty",
            "question_count_requested",
            "status",
            "score",
            "total_marks",
            "percentage",
            "started_at",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_class_arm_name(self, obj):
        return str(obj.class_arm) if obj.class_arm_id else None


class PracticeSessionDetailSerializer(PracticeSessionBaseSerializer):
    questions = serializers.SerializerMethodField()

    class Meta(PracticeSessionBaseSerializer.Meta):
        fields = PracticeSessionBaseSerializer.Meta.fields + ["questions"]

    def get_questions(self, obj):
        session_questions = obj.session_questions.select_related(
            "question",
        ).prefetch_related(
            "question__media",
        ).order_by("order")
        return PracticeQuestionSerializer(
            session_questions,
            many=True,
            context=self.context,
        ).data


class PracticeHistorySerializer(PracticeSessionBaseSerializer):
    pass


class PracticeAnswerInputSerializer(serializers.Serializer):
    session_question = serializers.PrimaryKeyRelatedField(
        queryset=PracticeSessionQuestion.objects.select_related(
            "session",
            "question",
        ).all(),
    )
    selected_option = serializers.PrimaryKeyRelatedField(
        queryset=QuestionOption.objects.select_related("question").all(),
    )


class PracticeSubmitSerializer(serializers.Serializer):
    answers = PracticeAnswerInputSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("At least one answer is required.")
        return value

    def create(self, validated_data):
        session = self.context["session"]
        try:
            return submit_practice_session(session, validated_data["answers"])
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


class PracticeResultOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    label = serializers.CharField(allow_blank=True)
    text = serializers.CharField(allow_blank=True)


class PracticeResultAnswerSerializer(serializers.ModelSerializer):
    session_question = serializers.IntegerField(source="session_question.id")
    question_text = serializers.CharField(
        source="session_question.question_text",
        read_only=True,
    )
    has_diagram = serializers.BooleanField(
        source="session_question.question.has_diagram",
        read_only=True,
    )
    diagram_description = serializers.CharField(
        source="session_question.question.diagram_description",
        read_only=True,
    )
    media = serializers.SerializerMethodField()
    selected_option = serializers.SerializerMethodField()
    correct_option = serializers.SerializerMethodField()
    explanation = serializers.CharField(
        source="session_question.explanation",
        read_only=True,
    )

    class Meta:
        model = PracticeAnswer
        fields = [
            "session_question",
            "question_text",
            "has_diagram",
            "diagram_description",
            "media",
            "selected_option",
            "correct_option",
            "is_correct",
            "marks_awarded",
            "explanation",
        ]
        read_only_fields = fields

    def get_media(self, answer):
        media = answer.session_question.question.media.filter(is_active=True).order_by(
            "-is_primary",
            "display_order",
            "id",
        )
        return StudentQuestionMediaSerializer(
            media,
            many=True,
            context=self.context,
        ).data

    def _snapshot_option(self, answer, label):
        for option in answer.session_question.options_snapshot:
            if option.get("label") == label:
                return {
                    "id": option.get("id"),
                    "label": option.get("label", ""),
                    "text": option.get("text", ""),
                }
        return None

    def get_selected_option(self, answer):
        option = self._snapshot_option(answer, answer.selected_label)
        if option is None and answer.selected_option_id:
            option = {
                "id": answer.selected_option_id,
                "label": answer.selected_option.label,
                "text": answer.selected_option.text,
            }
        return PracticeResultOptionSerializer(option).data if option else None

    def get_correct_option(self, answer):
        for option in answer.session_question.options_snapshot:
            if option.get("is_correct"):
                return PracticeResultOptionSerializer(
                    {
                        "id": option.get("id"),
                        "label": option.get("label", ""),
                        "text": option.get("text", ""),
                    }
                ).data
        return None


class PracticeResultSerializer(PracticeSessionBaseSerializer):
    answers = serializers.SerializerMethodField()

    class Meta(PracticeSessionBaseSerializer.Meta):
        fields = PracticeSessionBaseSerializer.Meta.fields + ["answers"]

    def to_representation(self, instance):
        try:
            get_practice_result(instance)
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
        return super().to_representation(instance)

    def get_answers(self, obj):
        answers = obj.answers.select_related(
            "selected_option",
            "session_question",
            "session_question__question",
        ).prefetch_related(
            "session_question__question__media",
        ).order_by("session_question__order")
        return PracticeResultAnswerSerializer(
            answers,
            many=True,
            context=self.context,
        ).data


class PracticeSummarySerializer(serializers.Serializer):
    total_sessions_completed = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    total_correct_answers = serializers.IntegerField()
    overall_average_percentage = serializers.FloatField(allow_null=True)
    best_percentage = serializers.FloatField(allow_null=True)
    lowest_percentage = serializers.FloatField(allow_null=True)
    last_practice_at = serializers.DateTimeField(allow_null=True)
    best_subject = serializers.CharField(allow_null=True)
    weakest_subject = serializers.CharField(allow_null=True)


class PracticeSubjectPerformanceSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    sessions_completed = serializers.IntegerField()
    questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    average_percentage = serializers.FloatField(allow_null=True)
    last_practiced_at = serializers.DateTimeField(allow_null=True)


class PracticeTopicPerformanceSerializer(serializers.Serializer):
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    sessions_completed = serializers.IntegerField()
    questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    average_percentage = serializers.FloatField(allow_null=True)
    last_practiced_at = serializers.DateTimeField(allow_null=True)
    strength_level = serializers.CharField()


class PracticeRecommendationSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()
    priority = serializers.CharField()
    reason = serializers.CharField()
    recommended_difficulty = serializers.CharField()
    available_question_count = serializers.IntegerField()
    suggested_question_count = serializers.IntegerField()


class PracticeRecentSessionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    topic_id = serializers.IntegerField(allow_null=True)
    topic_title = serializers.CharField(allow_null=True)
    difficulty = serializers.CharField()
    question_count_requested = serializers.IntegerField()
    score = serializers.IntegerField()
    total_marks = serializers.IntegerField()
    percentage = serializers.FloatField(allow_null=True)
    started_at = serializers.DateTimeField()
    submitted_at = serializers.DateTimeField(allow_null=True)


class LearningPathTopicPerformanceSummarySerializer(serializers.Serializer):
    sessions_completed = serializers.IntegerField()
    questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    average_percentage = serializers.FloatField(allow_null=True)
    strength_level = serializers.CharField()
    last_practiced_at = serializers.DateTimeField(allow_null=True)


class LearningPathActionPayloadSerializer(serializers.Serializer):
    subject = serializers.IntegerField()
    topic = serializers.IntegerField()
    class_level = serializers.IntegerField(allow_null=True)
    difficulty = serializers.CharField()
    question_count = serializers.IntegerField()


class LearningPathTopicCardSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    category = serializers.CharField()
    priority = serializers.CharField()
    reason = serializers.CharField()
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    topic_id = serializers.IntegerField()
    topic_title = serializers.CharField()
    class_level_id = serializers.IntegerField(allow_null=True)
    class_level_name = serializers.CharField(allow_null=True)
    difficulty = serializers.CharField()
    recommended_question_count = serializers.IntegerField()
    available_question_count = serializers.IntegerField()
    performance = LearningPathTopicPerformanceSummarySerializer()
    action_payload = LearningPathActionPayloadSerializer()


class LearningPathSerializer(serializers.Serializer):
    overall_status = serializers.CharField()
    headline = serializers.CharField()
    message = serializers.CharField()
    recommended_next_action = LearningPathTopicCardSerializer(allow_null=True)
    topic_cards = LearningPathTopicCardSerializer(many=True)
    summary = PracticeSummarySerializer()


class PracticeAnalyticsDashboardSerializer(serializers.Serializer):
    summary = PracticeSummarySerializer()
    subject_performance = PracticeSubjectPerformanceSerializer(many=True)
    topic_performance = PracticeTopicPerformanceSerializer(many=True)
    weak_topics = PracticeTopicPerformanceSerializer(many=True)
    strong_topics = PracticeTopicPerformanceSerializer(many=True)
    recommendations = PracticeRecommendationSerializer(many=True)
    recent_sessions = PracticeRecentSessionSerializer(many=True)
    message = serializers.CharField(allow_blank=True)
