from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.academics.models import ClassLevel, Subject, Topic
from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import (
    Question,
    QuestionDifficulty,
    QuestionImportBatch,
    QuestionImportFileType,
    QuestionImportRow,
    QuestionOption,
    QuestionOptionLabel,
    QuestionSource,
    QuestionSourceType,
)
from apps.question_bank.selectors import is_platform_admin
from apps.question_bank.services import (
    build_question_content_hash,
    create_pending_import_rows,
    load_csv_import_rows,
    validate_question_options,
)
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
            "content_hash",
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
            "content_hash",
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
            "content_hash",
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

        question.content_hash = build_question_content_hash(
            question_text=question.question_text,
            subject=question.subject,
            topic=question.topic,
            class_level=question.class_level,
            options=options_data,
        )
        try:
            question.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
        question.save(update_fields=["content_hash", "updated_at"])


class QuestionReviewSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)


class QuestionImportBatchSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = QuestionImportBatch
        fields = [
            "id",
            "school",
            "school_name",
            "uploaded_by",
            "uploaded_by_name",
            "source",
            "source_name",
            "title",
            "original_filename",
            "file_type",
            "status",
            "total_rows",
            "successful_rows",
            "failed_rows",
            "duplicate_rows",
            "error_summary",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class QuestionImportRowSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)

    class Meta:
        model = QuestionImportRow
        fields = [
            "id",
            "batch",
            "row_number",
            "raw_data",
            "status",
            "error_message",
            "question",
            "question_text",
            "content_hash",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class QuestionImportCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    source = serializers.PrimaryKeyRelatedField(
        queryset=QuestionSource.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        filename = getattr(value, "name", "")
        if not filename.lower().endswith(".csv"):
            raise serializers.ValidationError("Only CSV imports are supported for now.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        target_school = attrs.get("school")
        if is_platform_admin(user):
            return attrs

        if user.role == UserRole.SCHOOL_ADMIN:
            if not user.school_id:
                raise serializers.ValidationError(
                    {"school": "School admins must belong to a school."}
                )
            if target_school and target_school.id != user.school_id:
                raise serializers.ValidationError(
                    {"school": "School admins can only import for their own school."}
                )
            attrs["school"] = user.school
            return attrs

        allow_teacher_imports = self.context.get("allow_teacher_imports", False)
        if allow_teacher_imports and user.role == UserRole.TEACHER and user.school_id:
            if target_school and target_school.id != user.school_id:
                raise serializers.ValidationError(
                    {"school": "Teachers can only import for their own school."}
                )
            attrs["school"] = user.school
            return attrs

        raise serializers.ValidationError("You cannot import question bank content.")

    def create(self, validated_data):
        request = self.context["request"]
        uploaded_file = validated_data.pop("file")
        rows = load_csv_import_rows(uploaded_file)
        batch = QuestionImportBatch.objects.create(
            uploaded_by=request.user,
            school=validated_data.get("school"),
            source=validated_data.get("source"),
            title=validated_data["title"],
            original_filename=getattr(uploaded_file, "name", ""),
            file_type=QuestionImportFileType.CSV,
        )
        create_pending_import_rows(batch, rows)
        return batch


class ApprovedQuestionSearchSerializer(serializers.Serializer):
    subject = serializers.IntegerField(required=False)
    topic = serializers.IntegerField(required=False)
    class_level = serializers.IntegerField(required=False)
    difficulty = serializers.ChoiceField(
        choices=QuestionDifficulty.values,
        required=False,
    )
    source_type = serializers.ChoiceField(
        choices=QuestionSourceType.values,
        required=False,
    )
    exam_body = serializers.CharField(required=False, allow_blank=True)
    year = serializers.IntegerField(required=False)
    count = serializers.IntegerField(required=False, min_value=1, max_value=100)
    random = serializers.BooleanField(required=False, default=False)
