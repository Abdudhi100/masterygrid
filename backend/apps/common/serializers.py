"""Shared serializers for MasteryGrid APIs."""

from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()
    environment = serializers.CharField(allow_blank=True)
    version = serializers.CharField(allow_blank=True, required=False)
    timestamp = serializers.DateTimeField()
