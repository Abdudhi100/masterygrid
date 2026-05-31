from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.practice.analytics import (
    get_student_learning_path,
    get_student_practice_dashboard,
    get_student_practice_recommendations,
    get_student_practice_summary,
    get_student_strong_topics,
    get_student_subject_performance,
    get_student_topic_performance,
    get_student_weak_topics,
)
from apps.practice.models import PracticeSession
from apps.practice.permissions import (
    PracticeAnalyticsPermission,
    PracticeSessionPermission,
)
from apps.practice.selectors import get_practice_sessions_for_user
from apps.practice.serializers import (
    LearningPathSerializer,
    PracticeAnalyticsDashboardSerializer,
    PracticeHistorySerializer,
    PracticeRecommendationSerializer,
    PracticeResultSerializer,
    PracticeSessionDetailSerializer,
    PracticeStartSerializer,
    PracticeSubjectPerformanceSerializer,
    PracticeSummarySerializer,
    PracticeSubmitSerializer,
    PracticeTopicPerformanceSerializer,
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


class PracticeSummaryAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeSummarySerializer(
            get_student_practice_summary(request.user)
        )
        return Response(serializer.data)


class PracticeSubjectPerformanceAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeSubjectPerformanceSerializer(
            get_student_subject_performance(request.user),
            many=True,
        )
        return Response(serializer.data)


class PracticeTopicPerformanceAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeTopicPerformanceSerializer(
            get_student_topic_performance(request.user),
            many=True,
        )
        return Response(serializer.data)


class PracticeWeakTopicsAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeTopicPerformanceSerializer(
            get_student_weak_topics(request.user),
            many=True,
        )
        return Response(serializer.data)


class PracticeStrongTopicsAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeTopicPerformanceSerializer(
            get_student_strong_topics(request.user),
            many=True,
        )
        return Response(serializer.data)


class PracticeRecommendationsAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeRecommendationSerializer(
            get_student_practice_recommendations(request.user),
            many=True,
        )
        return Response(serializer.data)


class PracticeAnalyticsDashboardAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = PracticeAnalyticsDashboardSerializer(
            get_student_practice_dashboard(request.user)
        )
        return Response(serializer.data)


class PracticeLearningPathAPIView(APIView):
    permission_classes = [PracticeAnalyticsPermission]

    def get(self, request):
        serializer = LearningPathSerializer(get_student_learning_path(request.user))
        return Response(serializer.data)
