from rest_framework.permissions import BasePermission

from apps.common.choices import UserRole


class IsTeacherAnalyticsUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None)
            in {
                UserRole.PLATFORM_ADMIN,
                UserRole.SCHOOL_ADMIN,
                UserRole.TEACHER,
            }
        )


class IsTeacherOnlyAnalyticsUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == UserRole.TEACHER
            and getattr(user, "school_id", None)
        )


class IsSchoolAdminAnalyticsUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None)
            in {
                UserRole.PLATFORM_ADMIN,
                UserRole.SCHOOL_ADMIN,
            }
        )


class IsStudentAnalyticsUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == UserRole.STUDENT
            and getattr(user, "school_id", None)
        )
