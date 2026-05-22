from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.academics.models import LessonLog, Subject, Topic
from apps.academics.selectors import is_platform_admin
from apps.common.choices import UserRole


def get_object_school_id(obj):
    school_id = getattr(obj, "school_id", None)
    if school_id:
        return school_id
    return None


class AcademicRolePermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if is_platform_admin(user):
            return True

        model = getattr(view, "model", None)

        if request.method in SAFE_METHODS:
            return user.role in {
                UserRole.SCHOOL_ADMIN,
                UserRole.TEACHER,
                UserRole.STUDENT,
            }

        if user.role == UserRole.SCHOOL_ADMIN:
            return bool(user.school_id)

        if user.role == UserRole.TEACHER:
            return model is LessonLog and request.method in {"POST", "PUT", "PATCH"}

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_platform_admin(user):
            return True

        obj_school_id = get_object_school_id(obj)
        is_global_academic_content = isinstance(obj, (Subject, Topic)) and obj_school_id is None

        if request.method in SAFE_METHODS and is_global_academic_content:
            return user.role in {
                UserRole.SCHOOL_ADMIN,
                UserRole.TEACHER,
                UserRole.STUDENT,
            }

        if obj_school_id != user.school_id:
            return False

        if user.role == UserRole.SCHOOL_ADMIN:
            return True

        if user.role == UserRole.TEACHER:
            if request.method in SAFE_METHODS:
                return True
            return isinstance(obj, LessonLog) and obj.teacher_id == user.id

        if user.role == UserRole.STUDENT:
            return request.method in SAFE_METHODS

        return False
