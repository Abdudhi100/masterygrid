import logging
from collections.abc import Mapping

from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {
    "password",
    "token",
    "access",
    "refresh",
    "secret",
    "authorization",
    "api_key",
    "apikey",
}


def is_sensitive_key(key):
    normalized = str(key).lower().replace("-", "_")
    return any(sensitive in normalized for sensitive in SENSITIVE_KEYS)


def scrub_metadata(value):
    if isinstance(value, Mapping):
        return {
            str(key): "[redacted]" if is_sensitive_key(key) else scrub_metadata(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [scrub_metadata(item) for item in value]

    if isinstance(value, tuple):
        return [scrub_metadata(item) for item in value]

    return value


def client_ip_from_request(request):
    if not request:
        return None

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR")


def user_agent_from_request(request):
    if not request:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")[:1000]


def model_object_type(obj):
    if not obj:
        return ""
    meta = getattr(obj, "_meta", None)
    if not meta:
        return obj.__class__.__name__
    return f"{meta.app_label}.{meta.model_name}"


def infer_school(*, school=None, actor=None, obj=None, target_user=None):
    if school is not None:
        return school

    for candidate in (obj, target_user, actor):
        if not candidate:
            continue
        candidate_school = getattr(candidate, "school", None)
        if candidate_school is not None:
            return candidate_school
    return None


def record_audit_log(
    *,
    actor,
    action,
    category,
    obj=None,
    school=None,
    target_user=None,
    metadata=None,
    request=None,
):
    try:
        resolved_school = infer_school(
            school=school,
            actor=actor,
            obj=obj,
            target_user=target_user,
        )
        actor_email = getattr(actor, "email", "") if actor else ""
        actor_role = getattr(actor, "role", "") if actor else ""
        target_email = getattr(target_user, "email", "") if target_user else ""

        return AuditLog.objects.create(
            school=resolved_school,
            actor=actor if getattr(actor, "pk", None) else None,
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            category=category,
            object_type=model_object_type(obj),
            object_id=str(getattr(obj, "pk", "") or ""),
            object_repr=str(obj)[:255] if obj else "",
            target_user=target_user if getattr(target_user, "pk", None) else None,
            target_user_email=target_email,
            ip_address=client_ip_from_request(request),
            user_agent=user_agent_from_request(request),
            metadata=scrub_metadata(metadata or {}),
        )
    except Exception:  # pragma: no cover - intentionally non-blocking safety net.
        logger.exception("Unable to record audit log for action=%s", action)
        return None
