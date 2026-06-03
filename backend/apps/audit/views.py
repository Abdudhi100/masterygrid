from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.audit.models import AuditLog
from apps.audit.permissions import CanViewAuditLogs
from apps.audit.selectors import filter_audit_logs, get_audit_logs_for_user
from apps.audit.serializers import AuditLogSerializer
from apps.common.choices import UserRole


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [CanViewAuditLogs]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["created_at", "category", "action"]
    ordering = ["-created_at"]

    def get_queryset(self):
        school_id = None
        if (
            self.request.user.role == UserRole.PLATFORM_ADMIN
            or self.request.user.is_superuser
        ):
            school_id = self.request.query_params.get("school")

        queryset = get_audit_logs_for_user(self.request.user, school_id=school_id)
        return filter_audit_logs(queryset, self.request.query_params)
