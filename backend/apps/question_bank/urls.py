from rest_framework.routers import DefaultRouter

from apps.question_bank.views import QuestionSourceViewSet, QuestionViewSet

app_name = "question_bank"

router = DefaultRouter()
router.register("sources", QuestionSourceViewSet, basename="question-source")
router.register("questions", QuestionViewSet, basename="question")

urlpatterns = router.urls
