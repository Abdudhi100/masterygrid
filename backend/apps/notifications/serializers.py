from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source="recipient.full_name", read_only=True)
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "school",
            "school_name",
            "recipient",
            "recipient_name",
            "actor",
            "actor_name",
            "title",
            "message",
            "notification_type",
            "priority",
            "status",
            "target_url",
            "object_type",
            "object_id",
            "metadata",
            "read_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
