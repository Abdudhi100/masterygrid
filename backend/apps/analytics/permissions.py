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
