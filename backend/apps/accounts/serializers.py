from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import (
    StudentProfile,
    TeacherProfile,
    UserImportBatch,
    UserImportRow,
    UserImportType,
)
from apps.accounts.permissions import is_platform_admin
from apps.common.choices import UserRole
from apps.schools.models import School

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "school",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "created_at",
            "updated_at",
        ]


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.TEACHER, is_active=True),
    )
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "school",
            "school_name",
            "staff_id",
            "phone_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        school = attrs.get("school", getattr(self.instance, "school", None))

        if school is None and user is not None:
            school = user.school
            attrs["school"] = school

        if user is None or school is None:
            return attrs

        if user.role != UserRole.TEACHER:
            raise serializers.ValidationError({"user": "User must have teacher role."})

        if user.school_id != school.id:
            raise serializers.ValidationError(
                {"school": "Profile school must match the teacher's school."}
            )

        request = self.context.get("request")
        request_user = getattr(request, "user", None)
        is_platform_admin = bool(
            request_user
            and request_user.is_authenticated
            and (
                getattr(request_user, "role", None) == UserRole.PLATFORM_ADMIN
                or getattr(request_user, "is_superuser", False)
            )
        )
        if (
            request_user
            and request_user.is_authenticated
            and not is_platform_admin
            and getattr(request_user, "role", None) == UserRole.SCHOOL_ADMIN
            and school.id != request_user.school_id
        ):
            raise serializers.ValidationError(
                {"school": "You can only manage profiles in your school."}
            )

        return attrs


class StudentProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.STUDENT, is_active=True),
    )
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "school",
            "school_name",
            "admission_number",
            "guardian_name",
            "guardian_phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        school = attrs.get("school", getattr(self.instance, "school", None))

        if school is None and user is not None:
            school = user.school
            attrs["school"] = school

        if user is None or school is None:
            return attrs

        if user.role != UserRole.STUDENT:
            raise serializers.ValidationError({"user": "User must have student role."})

        if user.school_id != school.id:
            raise serializers.ValidationError(
                {"school": "Profile school must match the student's school."}
            )

        request = self.context.get("request")
        request_user = getattr(request, "user", None)
        is_platform_admin = bool(
            request_user
            and request_user.is_authenticated
            and (
                getattr(request_user, "role", None) == UserRole.PLATFORM_ADMIN
                or getattr(request_user, "is_superuser", False)
            )
        )
        if (
            request_user
            and request_user.is_authenticated
            and not is_platform_admin
            and getattr(request_user, "role", None) == UserRole.SCHOOL_ADMIN
            and school.id != request_user.school_id
        ):
            raise serializers.ValidationError(
                {"school": "You can only manage profiles in your school."}
            )

        return attrs


class CurrentUserSerializer(UserSerializer):
    teacher_profile = serializers.SerializerMethodField()
    student_profile = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "teacher_profile",
            "student_profile",
        ]

    def get_teacher_profile(self, user):
        if not hasattr(user, "teacher_profile"):
            return None
        return TeacherProfileSerializer(user.teacher_profile).data

    def get_student_profile(self, user):
        if not hasattr(user, "student_profile"):
            return None
        return StudentProfileSerializer(user.student_profile).data


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    staff_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    admission_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    guardian_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    guardian_phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "password",
            "role",
            "school",
            "staff_id",
            "phone_number",
            "admission_number",
            "guardian_name",
            "guardian_phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        role = attrs.get("role", UserRole.STUDENT)
        school = attrs.get("school")
        request = self.context.get("request")
        request_user = getattr(request, "user", None)
        is_existing_platform_admin = bool(
            request_user
            and request_user.is_authenticated
            and (
                getattr(request_user, "role", None) == UserRole.PLATFORM_ADMIN
                or getattr(request_user, "is_superuser", False)
            )
        )

        if role == UserRole.PLATFORM_ADMIN:
            if not is_existing_platform_admin:
                raise serializers.ValidationError(
                    {"role": "Platform admins must be created by an existing platform admin."}
                )

        if role != UserRole.PLATFORM_ADMIN and school is None:
            raise serializers.ValidationError(
                {"school": "School is required for school admins, teachers, and students."}
            )

        if (
            request_user
            and request_user.is_authenticated
            and not is_existing_platform_admin
            and getattr(request_user, "role", None) == UserRole.SCHOOL_ADMIN
            and school is not None
            and school.id != request_user.school_id
        ):
            raise serializers.ValidationError(
                {"school": "School admins can only register users in their own school."}
            )

        teacher_profile_fields = {
            "staff_id": attrs.get("staff_id", ""),
            "phone_number": attrs.get("phone_number", ""),
        }
        student_profile_fields = {
            "admission_number": attrs.get("admission_number", ""),
            "guardian_name": attrs.get("guardian_name", ""),
            "guardian_phone": attrs.get("guardian_phone", ""),
        }

        if role != UserRole.TEACHER and any(teacher_profile_fields.values()):
            raise serializers.ValidationError(
                {"staff_id": "Teacher profile fields require role=teacher."}
            )

        if role != UserRole.STUDENT and any(student_profile_fields.values()):
            raise serializers.ValidationError(
                {"admission_number": "Student profile fields require role=student."}
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        staff_id = validated_data.pop("staff_id", "")
        phone_number = validated_data.pop("phone_number", "")
        admission_number = validated_data.pop("admission_number", "")
        guardian_name = validated_data.pop("guardian_name", "")
        guardian_phone = validated_data.pop("guardian_phone", "")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)

        if user.role == UserRole.TEACHER and (staff_id or phone_number):
            if not staff_id:
                raise serializers.ValidationError(
                    {"staff_id": "Staff ID is required when creating a teacher profile."}
                )
            TeacherProfile.objects.create(
                user=user,
                school=user.school,
                staff_id=staff_id,
                phone_number=phone_number,
            )

        if user.role == UserRole.STUDENT and (
            admission_number or guardian_name or guardian_phone
        ):
            if not admission_number:
                raise serializers.ValidationError(
                    {
                        "admission_number": (
                            "Admission number is required when creating a student profile."
                        )
                    }
                )
            StudentProfile.objects.create(
                user=user,
                school=user.school,
                admission_number=admission_number,
                guardian_name=guardian_name,
                guardian_phone=guardian_phone,
            )

        return user


class TeacherListProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ["id", "staff_id", "phone_number"]
        read_only_fields = fields


class StudentListProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["id", "admission_number", "guardian_name", "guardian_phone"]
        read_only_fields = fields


class TeacherListSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    teacher_profile = TeacherListProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "role",
            "school",
            "school_name",
            "is_active",
            "teacher_profile",
        ]
        read_only_fields = fields


class StudentListSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    student_profile = StudentListProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "role",
            "school",
            "school_name",
            "is_active",
            "student_profile",
        ]
        read_only_fields = fields


class UserImportBatchSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = UserImportBatch
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


class UserImportRowSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserImportRow
        fields = [
            "id",
            "batch",
            "row_number",
            "status",
            "raw_data",
            "error_message",
            "warning_message",
            "user",
            "user_name",
            "user_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserImportUploadSerializer(serializers.Serializer):
    import_type = serializers.ChoiceField(choices=UserImportType.choices)
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
                    {"school": "Platform admins must choose a school for user imports."}
                )
            return attrs

        if user.role != UserRole.SCHOOL_ADMIN:
            raise serializers.ValidationError("You cannot import users.")

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
