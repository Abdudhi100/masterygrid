from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.academics.models import (
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
