from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.assignments.models import Assignment
from apps.assignments.selectors import is_platform_admin
from apps.common.choices import AssignmentStatus, UserRole


class AssignmentPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if is_platform_admin(user):
            return True

        if user.role == UserRole.STUDENT:
            return False

        if request.method in SAFE_METHODS:
            return user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}

        if getattr(view, "action", None) in {
            "create",
            "update",
            "partial_update",
            "destroy",
            "generate_from_topic",
            "publish",
            "close",
            "archive",
            "extend_deadline",
            "reopen",
        }:
            return user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_platform_admin(user):
            return True

        if not isinstance(obj, Assignment):
            return False

        if user.role == UserRole.SCHOOL_ADMIN:
            return obj.school_id == user.school_id

        if user.role == UserRole.TEACHER:
            if obj.school_id != user.school_id or obj.teacher_id != user.id:
                return False

            if request.method in SAFE_METHODS:
                return True

            if getattr(view, "action", None) in {
                "publish",
                "close",
                "archive",
                "destroy",
                "extend_deadline",
                "reopen",
            }:
                return True

            return obj.status == AssignmentStatus.DRAFT

        return False
