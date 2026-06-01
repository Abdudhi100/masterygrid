from apps.notifications.models import Notification, NotificationStatus


def get_user_notifications(user):
    if not user or not user.is_authenticated:
        return Notification.objects.none()
    return Notification.objects.select_related("school", "recipient", "actor").filter(
        recipient=user,
    )


def get_unread_count(user):
    return get_user_notifications(user).filter(status=NotificationStatus.UNREAD).count()
