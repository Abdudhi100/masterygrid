from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.academics.models import ClassLevel, Subject, Topic
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import (
    Question,
    QuestionOption,
    QuestionOptionLabel,
    QuestionSource,
)
from apps.question_bank.services import validate_question_options
from apps.schools.models import School

User = get_user_model()


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    raise serializers.ValidationError(exc.messages)


class QuestionSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionSource
        fields = [
            "id",
            "name",
            "source_type",
            "exam_body",
            "year",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "label",
            "text",
            "is_correct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_label(self, value):
        value = value.upper()
        if value not in QuestionOptionLabel.values:
            raise serializers.ValidationError("Option label must be one of A, B, C, or D.")
        return value

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Option text cannot be blank.")
        return value.strip()


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    class_level_name = serializers.CharField(source="class_level.name", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    source_type = serializers.CharField(source="source.source_type", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.full_name", read_only=True)
    is_usable_for_assignment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "school",
            "school_name",
            "subject",
            "subject_name",
            "topic",
            "topic_title",
            "class_level",
            "class_level_name",
            "source",
            "source_name",
            "source_type",
            "question_text",
            "explanation",
            "difficulty",
            "status",
            "created_by",
            "created_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "is_active",
            "is_usable_for_assignment",
            "options",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "is_usable_for_assignment",
            "created_at",
            "updated_at",
        ]


class QuestionCreateUpdateSerializer(QuestionSerializer):
    options = QuestionOptionSerializer(many=True, required=False)
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.filter(is_active=True),
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.filter(is_active=True),
    )
    class_level = serializers.PrimaryKeyRelatedField(
        queryset=ClassLevel.objects.filter(is_active=True),
    )
    source = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSource.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta(QuestionSerializer.Meta):
        read_only_fields = [
            "id",
            "created_by",
            "created_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "is_usable_for_assignment",
            "created_at",
            "updated_at",
        ]

    def validate_options(self, value):
        normalized_options = []
        for option in value:
            normalized_option = dict(option)
            normalized_option["label"] = normalized_option["label"].upper()
            normalized_option["text"] = normalized_option["text"].strip()
            normalized_options.append(normalized_option)

        try:
            validate_question_options(normalized_options)
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        return normalized_options

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if user.role == UserRole.STUDENT:
            raise serializers.ValidationError("Students cannot manage question bank content.")

        instance = self.instance
        role = getattr(user, "role", None)
        target_school = attrs.get("school", getattr(instance, "school", None))
        if (
            target_school is None
            and role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}
            and user.school_id
        ):
            target_school = user.school
            attrs["school"] = user.school

        if role == UserRole.TEACHER:
            if not user.school_id:
                raise serializers.ValidationError(
                    {"school": "Teacher-created questions must belong to a school."}
                )
            if target_school and target_school.id != user.school_id:
                raise serializers.ValidationError(
                    {"school": "Teachers can only create questions for their own school."}
                )
            requested_status = attrs.get(
                "status",
                getattr(instance, "status", QuestionStatus.DRAFT),
            )
            if requested_status != QuestionStatus.DRAFT:
                raise serializers.ValidationError(
                    {"status": "Teachers can only create or edit draft questions."}
                )

        elif role == UserRole.SCHOOL_ADMIN:
            if not user.school_id:
                raise serializers.ValidationError(
                    {"school": "School admins must belong to a school."}
                )
            if target_school is None:
                raise serializers.ValidationError(
                    {"school": "School admins cannot create or edit global questions."}
                )
            if target_school.id != user.school_id:
                raise serializers.ValidationError(
                    {"school": "School admins can only manage their own school's questions."}
                )

        elif role == UserRole.PLATFORM_ADMIN or getattr(user, "is_superuser", False):
            pass
        else:
            raise serializers.ValidationError("You cannot manage question bank content.")

        data = {}
        if instance:
            for field in [
                "school",
                "subject",
                "topic",
                "class_level",
                "source",
                "question_text",
                "explanation",
                "difficulty",
                "status",
                "created_by",
                "reviewed_by",
                "reviewed_at",
                "is_active",
            ]:
                data[field] = getattr(instance, field)
        data.update(attrs)

        question = Question(**data)
        if instance:
            question.pk = instance.pk

        try:
            question.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        options_data = validated_data.pop("options", None)
        if options_data is None:
            raise serializers.ValidationError(
                {"options": "Exactly four options are required."}
            )

        question = Question(**validated_data)
        try:
            question.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        question.save()
        self._replace_options(question, options_data)
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        instance.save()

        if options_data is not None:
            self._replace_options(instance, options_data)

        return instance

    def _replace_options(self, question, options_data):
        try:
            validate_question_options(options_data)
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        question.options.all().delete()

        for option_data in options_data:
            option = QuestionOption(question=question, **option_data)
            try:
                option.full_clean()
            except DjangoValidationError as exc:
                raise_drf_validation_error(exc)
            option.save()


class QuestionReviewSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)
