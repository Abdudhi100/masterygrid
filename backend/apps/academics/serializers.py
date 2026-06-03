from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.academics.models import (
    AcademicImportBatch,
    AcademicImportRow,
    AcademicImportType,
    AcademicSession,
    ClassArm,
    ClassLevel,
    LessonLog,
    StudentEnrollment,
    Subject,
    TeacherClassSubjectAssignment,
    Term,
    Topic,
)
from apps.academics.selectors import is_platform_admin
from apps.common.choices import UserRole
from apps.schools.models import School

User = get_user_model()


def raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict)
    raise serializers.ValidationError(exc.messages)


class CleanModelSerializer(serializers.ModelSerializer):
    def _clean_instance(self, instance):
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        self._clean_instance(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        self._clean_instance(instance)
        instance.save()
        return instance


class AcademicSessionSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = AcademicSession
        fields = [
            "id",
            "school",
            "school_name",
            "name",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TermSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    academic_session_name = serializers.CharField(
        source="academic_session.name",
        read_only=True,
    )

    class Meta:
        model = Term
        fields = [
            "id",
            "school",
            "school_name",
            "academic_session",
            "academic_session_name",
            "name",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClassLevelSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = ClassLevel
        fields = [
            "id",
            "school",
            "school_name",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClassArmSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    class_level_name = serializers.CharField(source="class_level.name", read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ClassArm
        fields = [
            "id",
            "school",
            "school_name",
            "class_level",
            "class_level_name",
            "name",
            "display_name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "display_name", "created_at", "updated_at"]

    def get_display_name(self, obj):
        return str(obj)


class SubjectSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    scope = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id",
            "school",
            "school_name",
            "scope",
            "name",
            "code",
            "description",
            "is_jamb_subject",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "scope", "created_at", "updated_at"]

    def get_scope(self, obj):
        return "school" if obj.school_id else "global"


class TopicSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    class_level_name = serializers.CharField(source="class_level.name", read_only=True)
    scope = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id",
            "school",
            "school_name",
            "scope",
            "subject",
            "subject_name",
            "class_level",
            "class_level_name",
            "title",
            "description",
            "curriculum_tags",
            "jamb_relevance_level",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "scope", "created_at", "updated_at"]

    def get_scope(self, obj):
        return "school" if obj.school_id else "global"


class TeacherClassSubjectAssignmentSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.TEACHER, is_active=True),
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    teacher_email = serializers.EmailField(source="teacher.email", read_only=True)
    class_arm_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    academic_session_name = serializers.CharField(
        source="academic_session.name",
        read_only=True,
    )
    term_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherClassSubjectAssignment
        fields = [
            "id",
            "school",
            "school_name",
            "teacher",
            "teacher_name",
            "teacher_email",
            "class_arm",
            "class_arm_name",
            "subject",
            "subject_name",
            "academic_session",
            "academic_session_name",
            "term",
            "term_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "school_name",
            "teacher_name",
            "teacher_email",
            "class_arm_name",
            "subject_name",
            "academic_session_name",
            "term_name",
            "created_at",
            "updated_at",
        ]

    def get_class_arm_name(self, obj):
        return str(obj.class_arm)

    def get_term_name(self, obj):
        return obj.term.get_name_display() if obj.term_id else None


class StudentEnrollmentSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.STUDENT, is_active=True),
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_email = serializers.EmailField(source="student.email", read_only=True)
    class_arm_name = serializers.SerializerMethodField()
    academic_session_name = serializers.CharField(
        source="academic_session.name",
        read_only=True,
    )
    term_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentEnrollment
        fields = [
            "id",
            "school",
            "school_name",
            "student",
            "student_name",
            "student_email",
            "class_arm",
            "class_arm_name",
            "academic_session",
            "academic_session_name",
            "term",
            "term_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "school_name",
            "student_name",
            "student_email",
            "class_arm_name",
            "academic_session_name",
            "term_name",
            "created_at",
            "updated_at",
        ]

    def get_class_arm_name(self, obj):
        return str(obj.class_arm)

    def get_term_name(self, obj):
        return obj.term.get_name_display() if obj.term_id else None


class LessonLogSerializer(CleanModelSerializer):
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.TEACHER, is_active=True),
        required=False,
    )
    school_name = serializers.CharField(source="school.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    teacher_email = serializers.EmailField(source="teacher.email", read_only=True)
    class_arm_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    academic_session_name = serializers.CharField(
        source="academic_session.name",
        read_only=True,
    )
    term_name = serializers.SerializerMethodField()
    can_generate_assignment = serializers.BooleanField(read_only=True)

    class Meta:
        model = LessonLog
        fields = [
            "id",
            "school",
            "school_name",
            "teacher",
            "teacher_name",
            "teacher_email",
            "class_arm",
            "class_arm_name",
            "subject",
            "subject_name",
            "topic",
            "topic_title",
            "academic_session",
            "academic_session_name",
            "term",
            "term_name",
            "taught_at",
            "notes",
            "can_generate_assignment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "school_name",
            "teacher_name",
            "teacher_email",
            "class_arm_name",
            "subject_name",
            "topic_title",
            "academic_session_name",
            "term_name",
            "can_generate_assignment",
            "created_at",
            "updated_at",
        ]

    def get_class_arm_name(self, obj):
        return str(obj.class_arm)

    def get_term_name(self, obj):
        return obj.term.get_name_display() if obj.term_id else None


class AcademicImportBatchSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = AcademicImportBatch
        fields = [
            "id",
            "school",
            "school_name",
            "uploaded_by",
            "uploaded_by_name",
            "import_type",
            "original_filename",
            "status",
            "total_rows",
            "successful_rows",
            "failed_rows",
            "duplicate_rows",
            "warning_rows",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AcademicImportRowSerializer(serializers.ModelSerializer):
    student_enrollment_display = serializers.SerializerMethodField()
    teacher_assignment_display = serializers.SerializerMethodField()

    class Meta:
        model = AcademicImportRow
        fields = [
            "id",
            "batch",
            "row_number",
            "status",
            "raw_data",
            "error_message",
            "warning_message",
            "student_enrollment",
            "student_enrollment_display",
            "teacher_assignment",
            "teacher_assignment_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_student_enrollment_display(self, obj):
        return str(obj.student_enrollment) if obj.student_enrollment_id else ""

    def get_teacher_assignment_display(self, obj):
        return str(obj.teacher_assignment) if obj.teacher_assignment_id else ""


class AcademicImportUploadSerializer(serializers.Serializer):
    import_type = serializers.ChoiceField(choices=AcademicImportType.choices)
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        filename = getattr(value, "name", "")
        if not filename.lower().endswith(".csv"):
            raise serializers.ValidationError("Only CSV imports are supported.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        target_school = attrs.get("school")
        if is_platform_admin(user):
            if not target_school:
                raise serializers.ValidationError(
                    {"school": "Platform admins must choose a school for academic imports."}
                )
            return attrs

        if user.role != UserRole.SCHOOL_ADMIN:
            raise serializers.ValidationError("You cannot import academic records.")

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
