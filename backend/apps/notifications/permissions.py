from rest_framework.permissions import BasePermission

from apps.notifications.models import Notification


class NotificationPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Notification):
            return False
        return obj.recipient_id == request.user.id
