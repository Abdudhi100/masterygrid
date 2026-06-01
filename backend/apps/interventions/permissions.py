from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.choices import UserRole
from apps.interventions.models import StudentIntervention
from apps.interventions.selectors import (
    is_platform_admin,
    teacher_can_access_student,
    user_can_access_student,
)


class InterventionPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                is_platform_admin(user)
                or user.role in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER}
            )
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not isinstance(obj, StudentIntervention):
            return False

        if is_platform_admin(user):
            return True

        if user.role == UserRole.SCHOOL_ADMIN:
            return bool(user.school_id and obj.school_id == user.school_id)

        if user.role == UserRole.TEACHER:
            if request.method in SAFE_METHODS:
                return teacher_can_access_student(user, obj.student)
            return teacher_can_access_student(user, obj.student)

        return False


def can_create_intervention_for_student(user, student):
    return user_can_access_student(user, student)
