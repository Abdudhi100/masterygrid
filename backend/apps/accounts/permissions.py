from rest_framework.permissions import BasePermission

from apps.common.choices import UserRole


def user_has_role(user, role):
    return bool(user and user.is_authenticated and getattr(user, "role", None) == role)


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "role", None) == UserRole.PLATFORM_ADMIN
                or getattr(request.user, "is_superuser", False)
            )
        )


class IsSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return user_has_role(request.user, UserRole.SCHOOL_ADMIN)


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return user_has_role(request.user, UserRole.TEACHER)


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return user_has_role(request.user, UserRole.STUDENT)


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(user, "is_superuser", False)
        )
    )


def is_school_admin(user):
    return user_has_role(user, UserRole.SCHOOL_ADMIN)


class IsSchoolUserManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return is_platform_admin(user) or is_school_admin(user)


class IsProfileOwnerOrSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if is_platform_admin(user) or is_school_admin(user):
            return True

        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return getattr(user, "role", None) in {UserRole.TEACHER, UserRole.STUDENT}

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if is_platform_admin(user):
            return True

        if is_school_admin(user):
            return obj.school_id == user.school_id

        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return obj.user_id == user.id

        return False
