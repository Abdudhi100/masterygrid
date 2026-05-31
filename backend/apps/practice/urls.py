from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.practice.views import (
    PracticeAnalyticsDashboardAPIView,
    PracticeLearningPathAPIView,
    PracticeRecommendationsAPIView,
    PracticeSessionViewSet,
    PracticeStrongTopicsAPIView,
    PracticeSubjectPerformanceAPIView,
    PracticeSummaryAPIView,
    PracticeTopicPerformanceAPIView,
    PracticeWeakTopicsAPIView,
)

app_name = "practice"

router = DefaultRouter()
router.register("sessions", PracticeSessionViewSet, basename="practice-session")

urlpatterns = [
    path(
        "analytics/summary/",
        PracticeSummaryAPIView.as_view(),
        name="practice-analytics-summary",
    ),
    path(
        "analytics/subjects/",
        PracticeSubjectPerformanceAPIView.as_view(),
        name="practice-analytics-subjects",
    ),
    path(
        "analytics/topics/",
        PracticeTopicPerformanceAPIView.as_view(),
        name="practice-analytics-topics",
    ),
    path(
        "analytics/weak-topics/",
        PracticeWeakTopicsAPIView.as_view(),
        name="practice-analytics-weak-topics",
    ),
    path(
        "analytics/strong-topics/",
        PracticeStrongTopicsAPIView.as_view(),
        name="practice-analytics-strong-topics",
    ),
    path(
        "analytics/recommendations/",
        PracticeRecommendationsAPIView.as_view(),
        name="practice-analytics-recommendations",
    ),
    path(
        "analytics/dashboard/",
        PracticeAnalyticsDashboardAPIView.as_view(),
        name="practice-analytics-dashboard",
    ),
    path(
        "learning-path/",
        PracticeLearningPathAPIView.as_view(),
        name="practice-learning-path",
    ),
    *router.urls,
]
