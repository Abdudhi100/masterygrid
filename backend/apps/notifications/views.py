from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notifications.models import NotificationStatus
from apps.notifications.permissions import NotificationPermission
from apps.notifications.selectors import get_unread_count, get_user_notifications
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import (
    archive_notification,
    mark_all_notifications_read,
    mark_notification_read,
    mark_notification_unread,
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [NotificationPermission]

    def get_queryset(self):
        queryset = get_user_notifications(self.request.user)
        params = self.request.query_params
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("notification_type"):
            queryset = queryset.filter(notification_type=params["notification_type"])
        if params.get("priority"):
            queryset = queryset.filter(priority=params["priority"])
        if params.get("created_after"):
            queryset = queryset.filter(created_at__gte=params["created_after"])
        if params.get("created_before"):
            queryset = queryset.filter(created_at__lte=params["created_before"])
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = mark_notification_read(self.get_object(), request.user)
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="mark-unread")
    def mark_unread(self, request, pk=None):
        notification = mark_notification_unread(self.get_object(), request.user)
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        notification = archive_notification(self.get_object(), request.user)
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated_count = mark_all_notifications_read(request.user)
        return Response({"updated_count": updated_count})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response({"unread_count": get_unread_count(request.user)})
