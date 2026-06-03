"""Serializers for school APIs."""

from rest_framework import serializers


class SchoolSetupStepSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    status = serializers.ChoiceField(choices=["complete", "incomplete", "warning"])
    count = serializers.IntegerField()
    required_count = serializers.IntegerField()
    action_url = serializers.CharField()
    recommendation = serializers.CharField()


class SchoolSetupStatusSerializer(serializers.Serializer):
    school_id = serializers.IntegerField()
    school_name = serializers.CharField()
    completion_percentage = serializers.IntegerField()
    is_setup_complete = serializers.BooleanField()
    steps = SchoolSetupStepSerializer(many=True)
    next_step = SchoolSetupStepSerializer(allow_null=True)
    blocking_issues = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())
