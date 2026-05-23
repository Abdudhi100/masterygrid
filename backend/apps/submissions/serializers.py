from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.assignments.models import Assignment, AssignmentQuestion
from apps.common.choices import SubmissionStatus
from apps.question_bank.models import QuestionOption
from apps.question_bank.serializers import StudentQuestionMediaSerializer
from apps.submissions.models import StudentAnswer, Submission
from apps.submissions.services import (
    create_or_get_submission,
    get_submission_questions_for_student,
    submit_assignment,
)


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    raise serializers.ValidationError(exc.messages)


class StudentQuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "label", "text"]
        read_only_fields = fields


class StudentSubmissionQuestionSerializer(serializers.Serializer):
    assignment_question = serializers.IntegerField(source="id")
    question = serializers.IntegerField(source="question.id")
    question_text = serializers.CharField(source="question.question_text")
    has_diagram = serializers.BooleanField(source="question.has_diagram")
    diagram_description = serializers.CharField(source="question.diagram_description")
    media = serializers.SerializerMethodField()
    marks = serializers.IntegerField()
    options = serializers.SerializerMethodField()

    def get_media(self, assignment_question):
        media = assignment_question.question.media.filter(is_active=True).order_by(
            "-is_primary",
            "display_order",
            "id",
        )
        return StudentQuestionMediaSerializer(
            media,
            many=True,
            context=self.context,
        ).data

    def get_options(self, assignment_question):
        options = assignment_question.question.options.order_by("label")
        return StudentQuestionOptionSerializer(options, many=True).data


class StudentAnswerSerializer(serializers.ModelSerializer):
    selected_option_label = serializers.CharField(
        source="selected_option.label",
        read_only=True,
    )

    class Meta:
        model = StudentAnswer
        fields = [
            "id",
            "submission",
            "assignment_question",
            "selected_option",
            "selected_option_label",
            "answered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "answered_at", "created_at", "updated_at"]


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    subject_name = serializers.CharField(source="assignment.subject.name", read_only=True)
    topic_title = serializers.CharField(source="assignment.topic.title", read_only=True)
    class_arm_name = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id",
            "school",
            "assignment",
            "assignment_title",
            "student",
            "student_name",
            "subject_name",
            "topic_title",
            "class_arm_name",
            "status",
            "started_at",
            "submitted_at",
            "graded_at",
            "score",
            "total_marks",
            "percentage",
            "time_spent_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_class_arm_name(self, obj):
        return str(obj.assignment.class_arm)


class SubmissionStartInputSerializer(serializers.Serializer):
    assignment = serializers.PrimaryKeyRelatedField(
        queryset=Assignment.objects.all(),
    )

    def create(self, validated_data):
        request = self.context["request"]
        try:
            return create_or_get_submission(
                student=request.user,
                assignment=validated_data["assignment"],
            )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


class SubmissionStartSerializer(SubmissionSerializer):
    questions = serializers.SerializerMethodField()

    class Meta(SubmissionSerializer.Meta):
        fields = SubmissionSerializer.Meta.fields + ["questions"]

    def get_questions(self, obj):
        assignment_questions = get_submission_questions_for_student(obj)
        return StudentSubmissionQuestionSerializer(
            assignment_questions,
            many=True,
            context=self.context,
        ).data


class SubmissionAnswerInputSerializer(serializers.Serializer):
    assignment_question = serializers.PrimaryKeyRelatedField(
        queryset=AssignmentQuestion.objects.select_related("assignment", "question").all(),
    )
    selected_option = serializers.PrimaryKeyRelatedField(
        queryset=QuestionOption.objects.select_related("question").all(),
    )


class SubmissionSubmitSerializer(serializers.Serializer):
    answers = SubmissionAnswerInputSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("At least one answer is required.")
        return value

    def create(self, validated_data):
        submission = self.context["submission"]
        try:
            return submit_assignment(submission, validated_data["answers"])
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


class ResultOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "label", "text"]
        read_only_fields = fields


class SubmissionResultAnswerSerializer(serializers.ModelSerializer):
    assignment_question = serializers.IntegerField(source="assignment_question.id")
    question_text = serializers.CharField(
        source="assignment_question.question.question_text",
        read_only=True,
    )
    has_diagram = serializers.BooleanField(
        source="assignment_question.question.has_diagram",
        read_only=True,
    )
    diagram_description = serializers.CharField(
        source="assignment_question.question.diagram_description",
        read_only=True,
    )
    media = serializers.SerializerMethodField()
    selected_option = ResultOptionSerializer(read_only=True)
    correct_option = serializers.SerializerMethodField()
    explanation = serializers.CharField(
        source="assignment_question.question.explanation",
        read_only=True,
    )

    class Meta:
        model = StudentAnswer
        fields = [
            "assignment_question",
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
        media = answer.assignment_question.question.media.filter(is_active=True).order_by(
            "-is_primary",
            "display_order",
            "id",
        )
        return StudentQuestionMediaSerializer(
            media,
            many=True,
            context=self.context,
        ).data

    def get_correct_option(self, answer):
        correct_option = (
            answer.assignment_question.question.options.filter(is_correct=True)
            .order_by("label")
            .first()
        )
        if correct_option is None:
            return None
        return ResultOptionSerializer(correct_option).data


class SubmissionResultSerializer(SubmissionSerializer):
    answers = serializers.SerializerMethodField()

    class Meta(SubmissionSerializer.Meta):
        fields = SubmissionSerializer.Meta.fields + ["answers"]

    def get_answers(self, obj):
        if obj.status not in {
            SubmissionStatus.GRADED,
            SubmissionStatus.AUTO_SUBMITTED,
        }:
            return []

        answer_map = {
            answer.assignment_question_id: answer
            for answer in obj.answers.select_related(
                "selected_option",
                "assignment_question",
                "assignment_question__question",
            ).prefetch_related(
                "assignment_question__question__options",
                "assignment_question__question__media",
            )
        }
        ordered_answers = [
            answer_map[item_id]
            for item_id in obj.question_order
            if item_id in answer_map
        ]
        return SubmissionResultAnswerSerializer(
            ordered_answers,
            many=True,
            context=self.context,
        ).data


class StudentAssignmentListSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    class_arm_name = serializers.SerializerMethodField()
    submission_id = serializers.SerializerMethodField()
    submission_status = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "instructions",
            "subject_name",
            "topic_title",
            "class_arm_name",
            "question_count",
            "duration_minutes",
            "starts_at",
            "due_at",
            "status",
            "submission_id",
            "submission_status",
        ]
        read_only_fields = fields

    def get_class_arm_name(self, obj):
        return str(obj.class_arm)

    def _get_submission(self, obj):
        submissions = getattr(obj, "student_submissions", None)
        if submissions is not None:
            return submissions[0] if submissions else None

        student = self.context.get("student")
        if student is None:
            return None
        return obj.submissions.filter(student=student).first()

    def get_submission_id(self, obj):
        submission = self._get_submission(obj)
        return submission.id if submission else None

    def get_submission_status(self, obj):
        submission = self._get_submission(obj)
        return submission.status if submission else None
