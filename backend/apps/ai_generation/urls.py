from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ai_generation.views import AIQuestionSuggestionRunViewSet

app_name = "ai_generation"

router = DefaultRouter()
router.register(
    "question-suggestions",
    AIQuestionSuggestionRunViewSet,
    basename="question-suggestions",
)

urlpatterns = [
    path("", include(router.urls)),
]
