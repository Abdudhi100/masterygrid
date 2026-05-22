from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.choices import UserRole
from apps.submissions.models import Submission
from apps.submissions.selectors import is_platform_admin


class SubmissionPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        action = getattr(view, "action", None)

        if action in {"start_assignment", "submit", "my_assignments"}:
            return user.role == UserRole.STUDENT

        if is_platform_admin(user):
            return True

        if action == "result":
            return user.role in {
                UserRole.SCHOOL_ADMIN,
                UserRole.TEACHER,
                UserRole.STUDENT,
            }

        if request.method in SAFE_METHODS:
            return user.role in {
                UserRole.SCHOOL_ADMIN,
                UserRole.TEACHER,
                UserRole.STUDENT,
            }

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not isinstance(obj, Submission):
            return False

        action = getattr(view, "action", None)
        if action == "submit":
            return obj.student_id == user.id and user.role == UserRole.STUDENT

        if is_platform_admin(user):
            return True

        if user.role == UserRole.SCHOOL_ADMIN:
            return obj.school_id == user.school_id

        if user.role == UserRole.TEACHER:
            return (
                obj.school_id == user.school_id
                and obj.assignment.teacher_id == user.id
                and request.method in SAFE_METHODS
            )

        if user.role == UserRole.STUDENT:
            if obj.student_id != user.id or obj.school_id != user.school_id:
                return False

            if action in {"retrieve", "result", "submit"}:
                return True
            return request.method in SAFE_METHODS

        return False
