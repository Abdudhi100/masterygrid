from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.academics.models import ClassArm, LessonLog, Subject, Topic
from apps.assignments.models import Assignment, AssignmentQuestion
from apps.assignments.services import (
    create_assignment_from_topic,
    validate_lesson_log_matches_assignment,
    validate_teacher_can_create_assignment,
)
from apps.common.choices import AssignmentStatus, UserRole
from apps.question_bank.models import Question
from apps.schools.models import School

User = get_user_model()


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    raise serializers.ValidationError(exc.messages)


class AssignmentQuestionSourceSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "difficulty",
            "source",
            "source_name",
        ]
        read_only_fields = fields


class AssignmentQuestionSerializer(serializers.ModelSerializer):
    question_detail = AssignmentQuestionSourceSerializer(source="question", read_only=True)

    class Meta:
        model = AssignmentQuestion
        fields = [
            "id",
            "assignment",
            "question",
            "question_detail",
            "order",
            "marks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    assignment_questions = AssignmentQuestionSerializer(many=True, read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    class_arm_name = serializers.SerializerMethodField()
    class_level_name = serializers.CharField(
        source="class_arm.class_level.name",
        read_only=True,
    )
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    lesson_log_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id",
            "school",
            "school_name",
            "teacher",
            "teacher_name",
            "class_arm",
            "class_arm_name",
            "class_level_name",
            "subject",
            "subject_name",
            "topic",
            "topic_title",
            "lesson_log",
            "lesson_log_display",
            "title",
            "instructions",
            "question_count",
            "duration_minutes",
            "starts_at",
            "due_at",
            "status",
            "status_display",
            "published_at",
            "assignment_questions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "school_name",
            "teacher_name",
            "class_arm_name",
            "class_level_name",
            "subject_name",
            "topic_title",
            "lesson_log_display",
            "status_display",
            "published_at",
            "assignment_questions",
            "created_at",
            "updated_at",
        ]

    def get_class_arm_name(self, obj):
        return str(obj.class_arm)

    def get_lesson_log_display(self, obj):
        if not obj.lesson_log_id:
            return None
        return str(obj.lesson_log)


class AssignmentCreateUpdateSerializer(AssignmentSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.TEACHER, is_active=True),
        required=False,
    )
    class_arm = serializers.PrimaryKeyRelatedField(
        queryset=ClassArm.objects.filter(is_active=True),
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.filter(is_active=True),
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.filter(is_active=True),
    )
    lesson_log = serializers.PrimaryKeyRelatedField(
        queryset=LessonLog.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta(AssignmentSerializer.Meta):
        read_only_fields = AssignmentSerializer.Meta.read_only_fields + [
            "status",
            "published_at",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = self.instance

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if instance and instance.status != AssignmentStatus.DRAFT:
            raise serializers.ValidationError(
                {"status": "Only draft assignments can be edited."}
            )

        data = {}
        if instance:
            for field in [
                "school",
                "teacher",
                "class_arm",
                "subject",
                "topic",
                "lesson_log",
                "title",
                "instructions",
                "question_count",
                "duration_minutes",
                "starts_at",
                "due_at",
                "status",
                "published_at",
            ]:
                data[field] = getattr(instance, field)
        data.update(attrs)

        if user.role == UserRole.TEACHER:
            data["teacher"] = user
            data["school"] = user.school
        elif user.role == UserRole.SCHOOL_ADMIN:
            data.setdefault("school", user.school)
            if data["school"].id != user.school_id:
                raise serializers.ValidationError(
                    {"school": "School admins can only manage their own school's assignments."}
                )
            if "teacher" not in data or data["teacher"] is None:
                raise serializers.ValidationError(
                    {"teacher": "Teacher is required for school admin assignment creation."}
                )
        elif user.role == UserRole.PLATFORM_ADMIN or getattr(user, "is_superuser", False):
            if "school" not in data or data["school"] is None:
                raise serializers.ValidationError({"school": "School is required."})
            if "teacher" not in data or data["teacher"] is None:
                raise serializers.ValidationError({"teacher": "Teacher is required."})
        else:
            raise serializers.ValidationError("You cannot manage assignments.")

        if data["teacher"].school_id != data["school"].id:
            raise serializers.ValidationError(
                {"teacher": "Teacher must belong to the selected school."}
            )

        try:
            validate_teacher_can_create_assignment(
                teacher=data["teacher"],
                class_arm=data["class_arm"],
                subject=data["subject"],
                topic=data["topic"],
            )
            if data.get("lesson_log"):
                validate_lesson_log_matches_assignment(
                    lesson_log=data["lesson_log"],
                    teacher=data["teacher"],
                    class_arm=data["class_arm"],
                    subject=data["subject"],
                    topic=data["topic"],
                )

            assignment = Assignment(**data)
            if instance:
                assignment.pk = instance.pk
            assignment.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        attrs["school"] = data["school"]
        attrs["teacher"] = data["teacher"]
        return attrs

    def create(self, validated_data):
        assignment = Assignment(**validated_data)
        try:
            assignment.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
        assignment.save()
        return assignment

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)
        instance.save()
        return instance


class AssignmentGenerateFromTopicSerializer(serializers.Serializer):
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.TEACHER, is_active=True),
        required=False,
    )
    class_arm = serializers.PrimaryKeyRelatedField(
        queryset=ClassArm.objects.filter(is_active=True),
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.filter(is_active=True),
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.filter(is_active=True),
    )
    lesson_log = serializers.PrimaryKeyRelatedField(
        queryset=LessonLog.objects.all(),
        required=False,
        allow_null=True,
    )
    title = serializers.CharField(max_length=255)
    instructions = serializers.CharField(required=False, allow_blank=True)
    question_count = serializers.IntegerField(min_value=1)
    duration_minutes = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    starts_at = serializers.DateTimeField(required=False, allow_null=True)
    due_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if user.role == UserRole.TEACHER:
            attrs["teacher"] = user
        elif user.role == UserRole.SCHOOL_ADMIN:
            teacher = attrs.get("teacher")
            if teacher is None:
                raise serializers.ValidationError(
                    {"teacher": "Teacher is required for school admin generation."}
                )
            if teacher.school_id != user.school_id:
                raise serializers.ValidationError(
                    {"teacher": "Teacher must belong to your school."}
                )
        elif user.role == UserRole.PLATFORM_ADMIN or getattr(user, "is_superuser", False):
            if attrs.get("teacher") is None:
                raise serializers.ValidationError({"teacher": "Teacher is required."})
        else:
            raise serializers.ValidationError("You cannot generate assignments.")

        if attrs.get("starts_at") and attrs.get("due_at") and attrs["starts_at"] > attrs["due_at"]:
            raise serializers.ValidationError(
                {"due_at": "Due date must be after start date."}
            )

        try:
            validate_teacher_can_create_assignment(
                teacher=attrs["teacher"],
                class_arm=attrs["class_arm"],
                subject=attrs["subject"],
                topic=attrs["topic"],
            )
            if attrs.get("lesson_log"):
                validate_lesson_log_matches_assignment(
                    lesson_log=attrs["lesson_log"],
                    teacher=attrs["teacher"],
                    class_arm=attrs["class_arm"],
                    subject=attrs["subject"],
                    topic=attrs["topic"],
                )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

        return attrs

    def create(self, validated_data):
        try:
            return create_assignment_from_topic(
                teacher=validated_data["teacher"],
                class_arm=validated_data["class_arm"],
                subject=validated_data["subject"],
                topic=validated_data["topic"],
                lesson_log=validated_data.get("lesson_log"),
                title=validated_data["title"],
                instructions=validated_data.get("instructions", ""),
                question_count=validated_data["question_count"],
                duration_minutes=validated_data.get("duration_minutes"),
                starts_at=validated_data.get("starts_at"),
                due_at=validated_data.get("due_at"),
            )
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


class AssignmentPublishSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)
