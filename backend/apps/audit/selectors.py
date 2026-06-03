from django.db.models import Q

from apps.audit.models import AuditLog
from apps.common.choices import UserRole


def is_platform_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (getattr(user, "is_superuser", False) or user.role == UserRole.PLATFORM_ADMIN)
    )


def get_audit_logs_for_user(user, school_id=None):
    queryset = AuditLog.objects.select_related(
        "school",
        "actor",
        "target_user",
    )

    if is_platform_admin(user):
        if school_id:
            return queryset.filter(school_id=school_id)
        return queryset

    if (
        user
        and user.is_authenticated
        and user.role == UserRole.SCHOOL_ADMIN
        and user.school_id
    ):
        return queryset.filter(school=user.school)

    return queryset.none()


def filter_audit_logs(queryset, params):
    if params.get("category"):
        queryset = queryset.filter(category=params["category"])
    if params.get("action"):
        queryset = queryset.filter(action=params["action"])
    if params.get("actor"):
        queryset = queryset.filter(actor_id=params["actor"])
    if params.get("target_user"):
        queryset = queryset.filter(target_user_id=params["target_user"])
    if params.get("object_type"):
        queryset = queryset.filter(object_type__icontains=params["object_type"])
    if params.get("date_from"):
        queryset = queryset.filter(created_at__date__gte=params["date_from"])
    if params.get("date_to"):
        queryset = queryset.filter(created_at__date__lte=params["date_to"])
    if params.get("search"):
        search = params["search"].strip()
        queryset = queryset.filter(
            Q(actor_email__icontains=search)
            | Q(target_user_email__icontains=search)
            | Q(action__icontains=search)
            | Q(category__icontains=search)
            | Q(object_type__icontains=search)
            | Q(object_id__icontains=search)
            | Q(object_repr__icontains=search)
        )
    return queryset
