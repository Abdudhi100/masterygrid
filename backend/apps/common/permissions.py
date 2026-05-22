"""Shared permission classes for MasteryGrid APIs."""

from rest_framework.permissions import BasePermission

from apps.common.choices import UserRole


class IsPlatformAdmin(BasePermission):
    """Placeholder permission for future platform administrator checks."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return bool(
            getattr(request.user, "role", None) == UserRole.PLATFORM_ADMIN
            or getattr(request.user, "is_superuser", False)
        )
