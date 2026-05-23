from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.practice.models import PracticeSession
from apps.practice.permissions import PracticeSessionPermission
from apps.practice.selectors import get_practice_sessions_for_user
from apps.practice.serializers import (
    PracticeHistorySerializer,
    PracticeResultSerializer,
    PracticeSessionDetailSerializer,
    PracticeStartSerializer,
    PracticeSubmitSerializer,
)


class PracticeSessionViewSet(viewsets.ReadOnlyModelViewSet):
    model = PracticeSession
    permission_classes = [PracticeSessionPermission]

    def get_queryset(self):
        return get_practice_sessions_for_user(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return PracticeHistorySerializer
        if self.action == "result":
            return PracticeResultSerializer
        return PracticeSessionDetailSerializer

    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        input_serializer = PracticeStartSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        input_serializer.is_valid(raise_exception=True)
        session = input_serializer.save()
        response_serializer = PracticeSessionDetailSerializer(
            session,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        session = self.get_object()
        serializer = PracticeSubmitSerializer(
            data=request.data,
            context={"request": request, "session": session},
        )
        serializer.is_valid(raise_exception=True)
        submitted_session = serializer.save()
        response_serializer = PracticeResultSerializer(
            submitted_session,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)

    @action(detail=True, methods=["get"])
    def result(self, request, pk=None):
        session = self.get_object()
        serializer = PracticeResultSerializer(
            session,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
