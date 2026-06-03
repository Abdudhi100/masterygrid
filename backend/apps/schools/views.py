"""Views for school APIs."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.schools.permissions import CanViewSchoolSetupStatus
from apps.schools.serializers import SchoolSetupStatusSerializer
from apps.schools.services import get_school_setup_status


class SchoolSetupStatusAPIView(APIView):
    permission_classes = [CanViewSchoolSetupStatus]

    def get(self, request):
        try:
            status = get_school_setup_status(
                request.user,
                school_id=request.query_params.get("school"),
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(exc.message_dict)
            raise ValidationError(exc.messages)

        serializer = SchoolSetupStatusSerializer(status)
        return Response(serializer.data)
