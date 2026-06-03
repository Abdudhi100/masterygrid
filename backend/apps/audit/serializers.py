from rest_framework import serializers

from apps.audit.models import AuditLog


def display_name(user):
    if not user:
        return ""
    return user.full_name or user.email


class AuditLogSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    actor_name = serializers.SerializerMethodField()
    target_user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "school",
            "school_name",
            "actor",
            "actor_name",
            "actor_email",
            "actor_role",
            "action",
            "category",
            "object_type",
            "object_id",
            "object_repr",
            "target_user",
            "target_user_name",
            "target_user_email",
            "ip_address",
            "user_agent",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        return display_name(obj.actor)

    def get_target_user_name(self, obj):
        return display_name(obj.target_user)
