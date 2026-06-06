"""Shared API views for MasteryGrid."""

from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework import status as drf_status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.serializers import HealthCheckSerializer


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        database_status = "ok"
        response_status = drf_status.HTTP_200_OK
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database_status = "unavailable"
            response_status = drf_status.HTTP_503_SERVICE_UNAVAILABLE

        payload = {
            "status": "ok" if database_status == "ok" else "error",
            "database": database_status,
            "environment": getattr(settings, "DJANGO_ENV", ""),
            "version": getattr(settings, "SPECTACULAR_SETTINGS", {}).get(
                "VERSION",
                "",
            ),
            "timestamp": timezone.now(),
        }
        serializer = HealthCheckSerializer(payload)
        return Response(serializer.data, status=response_status)
