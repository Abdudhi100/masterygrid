from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import User
from apps.common.choices import UserRole
from apps.interventions.models import (
    InterventionCategory,
    InterventionNote,
    InterventionPriority,
    InterventionSourceType,
    InterventionStatus,
    StudentIntervention,
)
from apps.interventions.permissions import can_create_intervention_for_student
from apps.interventions.selectors import is_platform_admin


def display_name(user):
    if not user:
        return ""
    return user.full_name or user.email


def active_class_arm_name(student):
    enrollment = (
        student.student_enrollments.select_related(
            "class_arm",
            "class_arm__class_level",
        )
        .filter(is_active=True)
        .order_by("-created_at")
        .first()
    )
    return str(enrollment.class_arm) if enrollment else ""


def admission_number(student):
    profile = getattr(student, "student_profile", None)
    return getattr(profile, "admission_number", None)


class InterventionNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = InterventionNote
        fields = [
            "id",
            "intervention",
            "author",
            "author_name",
            "note",
            "is_internal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "intervention",
            "author",
            "author_name",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        return display_name(obj.author)


class InterventionNoteCreateSerializer(serializers.Serializer):
    note = serializers.CharField()
    is_internal = serializers.BooleanField(required=False, default=True)


class StudentInterventionListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_class_arm = serializers.SerializerMethodField()
    student_admission_number = serializers.SerializerMethodField()
    school_name = serializers.CharField(source="school.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    source_assignment_title = serializers.CharField(
        source="source_assignment.title",
        read_only=True,
        allow_null=True,
    )
    source_subject_name = serializers.CharField(
        source="source_subject.name",
        read_only=True,
        allow_null=True,
    )
    source_topic_title = serializers.CharField(
        source="source_topic.title",
        read_only=True,
        allow_null=True,
    )
    source_class_arm_name = serializers.SerializerMethodField()
    notes_count = serializers.IntegerField(source="notes.count", read_only=True)

    class Meta:
        model = StudentIntervention
        fields = [
            "id",
            "school",
            "school_name",
            "student",
            "student_name",
            "student_email",
            "student_admission_number",
            "student_class_arm",
            "created_by",
            "created_by_name",
            "assigned_to",
            "assigned_to_name",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "source_type",
            "source_assignment",
            "source_assignment_title",
            "source_subject",
            "source_subject_name",
            "source_topic",
            "source_topic_title",
            "source_class_arm",
            "source_class_arm_name",
            "due_date",
            "completed_at",
            "notes_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "created_by", "created_at", "updated_at"]

    def get_student_name(self, obj):
        return display_name(obj.student)

    def get_student_class_arm(self, obj):
        return active_class_arm_name(obj.student)

    def get_student_admission_number(self, obj):
        return admission_number(obj.student)

    def get_created_by_name(self, obj):
        return display_name(obj.created_by)

    def get_assigned_to_name(self, obj):
        return display_name(obj.assigned_to)

    def get_source_class_arm_name(self, obj):
        return str(obj.source_class_arm) if obj.source_class_arm_id else ""


class StudentInterventionDetailSerializer(StudentInterventionListSerializer):
    notes = InterventionNoteSerializer(many=True, read_only=True)

    class Meta(StudentInterventionListSerializer.Meta):
        fields = [*StudentInterventionListSerializer.Meta.fields, "notes"]


class StudentInterventionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentIntervention
        fields = [
            "student",
            "assigned_to",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "source_type",
            "source_assignment",
            "source_subject",
            "source_topic",
            "source_class_arm",
            "due_date",
        ]

    def validate_student(self, student):
        if student.role != UserRole.STUDENT:
            raise serializers.ValidationError("Intervention target must be a student.")

        user = self.context["request"].user
        if not can_create_intervention_for_student(user, student):
            raise serializers.ValidationError(
                "You cannot create or update interventions for this student."
            )
        return student

    def validate_assigned_to(self, assigned_to):
        if assigned_to and assigned_to.role == UserRole.STUDENT:
            raise serializers.ValidationError("Interventions cannot be assigned to students.")
        return assigned_to

    def validate(self, attrs):
        user = self.context["request"].user
        instance = getattr(self, "instance", None)
        student = attrs.get("student") or getattr(instance, "student", None)
        assigned_to = attrs.get("assigned_to", getattr(instance, "assigned_to", None))

        if not student:
            raise serializers.ValidationError({"student": "A student is required."})

        if assigned_to and not is_platform_admin(assigned_to):
            if assigned_to.school_id != student.school_id:
                raise serializers.ValidationError(
                    {"assigned_to": "Assigned user must belong to the student's school."}
                )

        if user.role == UserRole.TEACHER and assigned_to:
            # Teachers may assign to themselves or leave it for a school admin to route.
            if assigned_to.id != user.id:
                raise serializers.ValidationError(
                    {"assigned_to": "Teachers can only assign interventions to themselves."}
                )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        student = validated_data["student"]
        intervention = StudentIntervention(
            **validated_data,
            school=student.school,
            created_by=user,
        )
        try:
            intervention.save()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return intervention

    def update(self, instance, validated_data):
        if "student" in validated_data and validated_data["student"].id != instance.student_id:
            raise serializers.ValidationError(
                {"student": "The student for an intervention cannot be changed."}
            )

        for field, value in validated_data.items():
            setattr(instance, field, value)
        try:
            instance.save()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return instance


class CreateFromProgressReportSerializer(serializers.Serializer):
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        choices=InterventionPriority.choices,
        default=InterventionPriority.MEDIUM,
    )
    category = serializers.ChoiceField(
        choices=InterventionCategory.choices,
        default=InterventionCategory.ACADEMIC_SUPPORT,
    )
    due_date = serializers.DateField(required=False, allow_null=True)
    recommended_action = serializers.CharField(required=False, allow_blank=True)
    source_subject = serializers.IntegerField(required=False, allow_null=True)
    source_topic = serializers.IntegerField(required=False, allow_null=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.exclude(role=UserRole.STUDENT),
        required=False,
        allow_null=True,
    )

    def validate_student(self, student):
        user = self.context["request"].user
        if student.role != UserRole.STUDENT:
            raise serializers.ValidationError("Intervention target must be a student.")
        if not can_create_intervention_for_student(user, student):
            raise serializers.ValidationError(
                "You cannot create interventions for this student."
            )
        return student

    def create(self, validated_data):
        from apps.academics.models import Subject, Topic

        user = self.context["request"].user
        student = validated_data["student"]
        subject_id = validated_data.pop("source_subject", None)
        topic_id = validated_data.pop("source_topic", None)
        recommended_action = validated_data.pop("recommended_action", "")
        source_subject = None
        source_topic = None
        if subject_id:
            source_subject = Subject.objects.filter(pk=subject_id).first()
        if topic_id:
            source_topic = Topic.objects.filter(pk=topic_id).first()

        description = validated_data.get("description", "")
        if recommended_action:
            description = f"{description}\n\nRecommended action: {recommended_action}".strip()

        intervention = StudentIntervention(
            school=student.school,
            student=student,
            created_by=user,
            assigned_to=validated_data.get("assigned_to"),
            title=validated_data["title"],
            description=description,
            category=validated_data.get("category", InterventionCategory.ACADEMIC_SUPPORT),
            priority=validated_data["priority"],
            status=InterventionStatus.OPEN,
            source_type=InterventionSourceType.PROGRESS_REPORT,
            source_subject=source_subject,
            source_topic=source_topic,
            due_date=validated_data.get("due_date"),
        )
        try:
            intervention.save()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return intervention
