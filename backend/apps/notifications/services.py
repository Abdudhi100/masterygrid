import logging

from django.db import transaction
from django.utils import timezone

from apps.academics.models import StudentEnrollment
from apps.accounts.models import User
from apps.common.choices import UserRole
from apps.notifications.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)

logger = logging.getLogger(__name__)


def create_notification(
    *,
    recipient,
    title,
    message="",
    notification_type=NotificationType.SYSTEM,
    priority=NotificationPriority.NORMAL,
    actor=None,
    school=None,
    target_url="",
    object_type="",
    object_id="",
    metadata=None,
):
    notification = Notification(
        school=school or getattr(recipient, "school", None),
        recipient=recipient,
        actor=actor,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        target_url=target_url,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        metadata=metadata or {},
    )
    notification.save()
    return notification


def create_bulk_notifications(recipients, **kwargs):
    notifications = []
    for recipient in recipients:
        notifications.append(create_notification(recipient=recipient, **kwargs))
    return notifications


def safe_create_notification(**kwargs):
    try:
        return create_notification(**kwargs)
    except Exception:
        logger.exception("Failed to create notification.")
        return None


def safe_create_bulk_notifications(recipients, **kwargs):
    notifications = []
    for recipient in recipients:
        notification = safe_create_notification(recipient=recipient, **kwargs)
        if notification:
            notifications.append(notification)
    return notifications


def _ensure_recipient(notification, user):
    if notification.recipient_id != user.id:
        raise PermissionError("You do not have access to this notification.")


def mark_notification_read(notification, user):
    _ensure_recipient(notification, user)
    notification.status = NotificationStatus.READ
    notification.read_at = notification.read_at or timezone.now()
    notification.save(update_fields=["status", "read_at", "updated_at"])
    return notification


def mark_notification_unread(notification, user):
    _ensure_recipient(notification, user)
    notification.status = NotificationStatus.UNREAD
    notification.read_at = None
    notification.save(update_fields=["status", "read_at", "updated_at"])
    return notification


def archive_notification(notification, user):
    _ensure_recipient(notification, user)
    notification.status = NotificationStatus.ARCHIVED
    notification.save(update_fields=["status", "updated_at"])
    return notification


def mark_all_notifications_read(user):
    now = timezone.now()
    with transaction.atomic():
        return Notification.objects.filter(
            recipient=user,
            status=NotificationStatus.UNREAD,
        ).update(status=NotificationStatus.READ, read_at=now, updated_at=now)


def notify_assignment_published(assignment, actor=None):
    students = _assignment_recipient_students(assignment)
    return safe_create_bulk_notifications(
        students,
        title="New assignment published",
        message=f"{assignment.title} is now available.",
        notification_type=NotificationType.ASSIGNMENT_PUBLISHED,
        priority=NotificationPriority.NORMAL,
        actor=actor or assignment.teacher,
        school=assignment.school,
        target_url=f"/student/assignments/{assignment.id}",
        object_type="assignment",
        object_id=assignment.id,
        metadata={
            "assignment_id": assignment.id,
            "subject": assignment.subject.name,
            "topic": assignment.topic.title,
        },
    )


def _assignment_recipient_students(assignment):
    return User.objects.filter(
        id__in=StudentEnrollment.objects.filter(
            school=assignment.school,
            class_arm=assignment.class_arm,
            is_active=True,
        ).values("student_id"),
        is_active=True,
        role=UserRole.STUDENT,
    )


def notify_assignment_deadline_extended(assignment, actor=None):
    students = _assignment_recipient_students(assignment)
    return safe_create_bulk_notifications(
        students,
        title="Assignment deadline extended",
        message=f"The deadline for {assignment.title} has been extended.",
        notification_type=NotificationType.ASSIGNMENT_DEADLINE_EXTENDED,
        priority=NotificationPriority.NORMAL,
        actor=actor or assignment.teacher,
        school=assignment.school,
        target_url=f"/student/assignments/{assignment.id}",
        object_type="assignment",
        object_id=assignment.id,
        metadata={
            "assignment_id": assignment.id,
            "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
            "late_submission_deadline": (
                assignment.late_submission_deadline.isoformat()
                if assignment.late_submission_deadline
                else None
            ),
        },
    )


def notify_assignment_reopened(assignment, actor=None):
    students = _assignment_recipient_students(assignment)
    return safe_create_bulk_notifications(
        students,
        title="Assignment reopened",
        message=f"{assignment.title} has been reopened.",
        notification_type=NotificationType.ASSIGNMENT_REOPENED,
        priority=NotificationPriority.NORMAL,
        actor=actor or assignment.teacher,
        school=assignment.school,
        target_url=f"/student/assignments/{assignment.id}",
        object_type="assignment",
        object_id=assignment.id,
        metadata={
            "assignment_id": assignment.id,
            "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
        },
    )


def notify_assignment_submitted(submission):
    assignment = submission.assignment
    return safe_create_notification(
        recipient=assignment.teacher,
        actor=submission.student,
        school=submission.school,
        title="Assignment submitted",
        message=f"{submission.student.full_name} submitted {assignment.title}.",
        notification_type=NotificationType.ASSIGNMENT_SUBMITTED,
        priority=NotificationPriority.NORMAL,
        target_url=f"/teacher/assignments/{assignment.id}/results",
        object_type="submission",
        object_id=submission.id,
        metadata={
            "assignment_id": assignment.id,
            "submission_id": submission.id,
            "student_id": submission.student_id,
            "percentage": float(submission.percentage),
        },
    )


def _intervention_target_url(user, intervention):
    role = getattr(user, "role", "")
    if role == UserRole.TEACHER:
        return f"/teacher/interventions/{intervention.id}"
    if role in {UserRole.SCHOOL_ADMIN, UserRole.PLATFORM_ADMIN}:
        return f"/admin/interventions/{intervention.id}"
    return ""


def notify_intervention_created(intervention):
    recipients = []
    if (
        intervention.assigned_to_id
        and intervention.assigned_to_id != intervention.created_by_id
    ):
        recipients.append(intervention.assigned_to)

    if intervention.priority in {
        "high",
        "urgent",
        NotificationPriority.HIGH,
        NotificationPriority.URGENT,
    }:
        admins = User.objects.filter(
            school=intervention.school,
            role=UserRole.SCHOOL_ADMIN,
            is_active=True,
        ).exclude(id=intervention.created_by_id)
        recipients.extend(admins)

    sent = []
    seen = set()
    for recipient in recipients:
        if not recipient or recipient.id in seen:
            continue
        seen.add(recipient.id)
        notification = safe_create_notification(
            recipient=recipient,
            actor=intervention.created_by,
            school=intervention.school,
            title="Intervention created",
            message=f"{intervention.title} was created for {intervention.student.full_name}.",
            notification_type=NotificationType.INTERVENTION_CREATED,
            priority=(
                NotificationPriority.HIGH
                if intervention.priority in {"high", "urgent"}
                else NotificationPriority.NORMAL
            ),
            target_url=_intervention_target_url(recipient, intervention),
            object_type="student_intervention",
            object_id=intervention.id,
            metadata={
                "intervention_id": intervention.id,
                "student_id": intervention.student_id,
                "priority": intervention.priority,
            },
        )
        if notification:
            sent.append(notification)
    return sent


def notify_intervention_note_added(intervention, note):
    recipients = []
    if intervention.created_by_id and intervention.created_by_id != note.author_id:
        recipients.append(intervention.created_by)
    if intervention.assigned_to_id and intervention.assigned_to_id != note.author_id:
        recipients.append(intervention.assigned_to)

    sent = []
    seen = set()
    for recipient in recipients:
        if not recipient or recipient.id in seen:
            continue
        seen.add(recipient.id)
        notification = safe_create_notification(
            recipient=recipient,
            actor=note.author,
            school=intervention.school,
            title="Intervention note added",
            message=f"A new note was added to {intervention.title}.",
            notification_type=NotificationType.INTERVENTION_NOTE_ADDED,
            priority=NotificationPriority.NORMAL,
            target_url=_intervention_target_url(recipient, intervention),
            object_type="intervention_note",
            object_id=note.id,
            metadata={
                "intervention_id": intervention.id,
                "note_id": note.id,
                "student_id": intervention.student_id,
            },
        )
        if notification:
            sent.append(notification)
    return sent
