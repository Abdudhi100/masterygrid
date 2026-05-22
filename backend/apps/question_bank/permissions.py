from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import Question, QuestionSource
from apps.question_bank.selectors import is_platform_admin


class QuestionBankPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.role == UserRole.STUDENT:
            return False

        if is_platform_admin(user):
            return True

        model = getattr(view, "model", None)

        if model is QuestionSource:
            return request.method in SAFE_METHODS

        if model is Question:
            if request.method in SAFE_METHODS:
                return user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}

            if getattr(view, "action", None) in {"approve", "reject", "archive"}:
                return user.role == UserRole.SCHOOL_ADMIN

            return user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_platform_admin(user):
            return True

        if isinstance(obj, QuestionSource):
            return request.method in SAFE_METHODS

        if not isinstance(obj, Question):
            return False

        if user.role == UserRole.SCHOOL_ADMIN:
            if request.method in SAFE_METHODS:
                return obj.school_id is None or obj.school_id == user.school_id

            return obj.school_id == user.school_id

        if user.role == UserRole.TEACHER:
            if request.method in SAFE_METHODS:
                return (
                    (
                        obj.school_id is None
                        and obj.status == QuestionStatus.APPROVED
                        and obj.is_active
                    )
                    or obj.school_id == user.school_id
                )

            if getattr(view, "action", None) in {"approve", "reject", "archive", "destroy"}:
                return False

            return (
                obj.school_id == user.school_id
                and obj.created_by_id == user.id
                and obj.status == QuestionStatus.DRAFT
            )

        return False
