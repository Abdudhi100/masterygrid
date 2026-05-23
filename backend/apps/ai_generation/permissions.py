from django.conf import settings
from rest_framework.permissions import BasePermission

from apps.ai_generation.models import AIQuestionSuggestionRun
from apps.common.choices import UserRole
from apps.question_bank.selectors import is_platform_admin


class CanRequestQuestionAISuggestion(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.role == UserRole.STUDENT:
            return False

        if is_platform_admin(user):
            return True

        if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
            return True

        return bool(
            user.role == UserRole.TEACHER
            and user.school_id
            and settings.AI_ALLOW_TEACHER_SUGGESTIONS
        )


class CanApplyQuestionAISuggestion(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == UserRole.STUDENT:
            return False
        if is_platform_admin(user):
            return True
        if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
            return True
        return bool(
            user.role == UserRole.TEACHER
            and user.school_id
            and settings.AI_ALLOW_TEACHER_APPLY_SUGGESTIONS
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_platform_admin(user):
            return True

        if not isinstance(obj, AIQuestionSuggestionRun):
            return False

        if user.role == UserRole.SCHOOL_ADMIN:
            return obj.school_id == user.school_id

        if user.role == UserRole.TEACHER:
            return bool(
                settings.AI_ALLOW_TEACHER_APPLY_SUGGESTIONS
                and obj.school_id == user.school_id
                and obj.requested_by_id == user.id
            )

        return False
