from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.choices import QuestionStatus, UserRole
from apps.question_bank.models import (
    Question,
    QuestionImportBatch,
    QuestionMedia,
    QuestionSource,
)
from apps.question_bank.selectors import is_platform_admin


def can_manage_question_media(question, user):
    if not user or not user.is_authenticated:
        return False

    if is_platform_admin(user):
        return True

    if user.role == UserRole.SCHOOL_ADMIN:
        return question.school_id is not None and question.school_id == user.school_id

    if user.role == UserRole.TEACHER:
        return (
            question.school_id == user.school_id
            and question.created_by_id == user.id
            and question.status == QuestionStatus.DRAFT
        )

    return False


def can_view_question_media(question, user):
    if not user or not user.is_authenticated:
        return False

    if is_platform_admin(user):
        return True

    if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
        return question.school_id is None or question.school_id == user.school_id

    if user.role == UserRole.TEACHER and user.school_id:
        return (
            (
                question.school_id is None
                and question.status == QuestionStatus.APPROVED
                and question.is_active
            )
            or question.school_id == user.school_id
        )

    return False


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

        if model is QuestionMedia:
            return user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}

        return False


class QuestionMediaPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == UserRole.STUDENT:
            return False
        return is_platform_admin(user) or user.role in {
            UserRole.SCHOOL_ADMIN,
            UserRole.TEACHER,
        }

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, QuestionMedia):
            return False

        if request.method in SAFE_METHODS:
            return can_view_question_media(obj.question, request.user)

        return can_manage_question_media(obj.question, request.user)


class CanImportQuestions(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if is_platform_admin(user):
            return True

        if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
            return True

        allow_teacher_imports = getattr(view, "allow_teacher_imports", False)
        return bool(
            allow_teacher_imports
            and user.role == UserRole.TEACHER
            and user.school_id
        )


class CanViewQuestionImports(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if is_platform_admin(user):
            return True
        if user.role == UserRole.SCHOOL_ADMIN and user.school_id:
            return True

        allow_teacher_imports = getattr(view, "allow_teacher_imports", False)
        return bool(
            allow_teacher_imports
            and user.role == UserRole.TEACHER
            and user.school_id
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_platform_admin(user):
            return True

        if not isinstance(obj, QuestionImportBatch):
            return False

        if user.role == UserRole.SCHOOL_ADMIN:
            return obj.school_id == user.school_id

        if user.role == UserRole.TEACHER:
            allow_teacher_imports = getattr(view, "allow_teacher_imports", False)
            return (
                allow_teacher_imports
                and obj.school_id == user.school_id
                and obj.uploaded_by_id == user.id
            )

        return False


class CanSearchApprovedQuestions(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if is_platform_admin(user):
            return True

        return user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER} and bool(
            user.school_id
        )

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


class CanViewQuestionQualityDashboard(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if is_platform_admin(user):
            return True
        return user.role == UserRole.SCHOOL_ADMIN and bool(user.school_id)


class CanBulkReviewQuestions(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if is_platform_admin(user):
            return True
        return user.role == UserRole.SCHOOL_ADMIN and bool(user.school_id)
