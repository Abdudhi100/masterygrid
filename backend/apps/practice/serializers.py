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
    options = serializers.SerializerMethodField()

    class Meta:
        model = PracticeSessionQuestion
        fields = [
            "session_question",
            "order",
            "question_text",
            "marks",
            "options",
        ]
        read_only_fields = fields

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
        session_questions = obj.session_questions.order_by("order")
        return PracticeQuestionSerializer(session_questions, many=True).data


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
            "selected_option",
            "correct_option",
            "is_correct",
            "marks_awarded",
            "explanation",
        ]
        read_only_fields = fields

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
        ).order_by("session_question__order")
        return PracticeResultAnswerSerializer(answers, many=True).data
