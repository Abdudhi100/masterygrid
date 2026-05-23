from rest_framework.permissions import BasePermission

from apps.common.choices import UserRole
from apps.practice.models import PracticeSession


class PracticeSessionPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role == UserRole.STUDENT
            and user.school_id
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not isinstance(obj, PracticeSession):
            return False

        return bool(
            user
            and user.is_authenticated
            and user.role == UserRole.STUDENT
            and obj.student_id == user.id
            and obj.school_id == user.school_id
        )
