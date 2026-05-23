from rest_framework.routers import DefaultRouter

from apps.question_bank.views import (
    QuestionImportBatchViewSet,
    QuestionMediaViewSet,
    QuestionSourceViewSet,
    QuestionViewSet,
)

app_name = "question_bank"

router = DefaultRouter()
router.register("sources", QuestionSourceViewSet, basename="question-source")
router.register("questions", QuestionViewSet, basename="question")
router.register("media", QuestionMediaViewSet, basename="question-media")
router.register("imports", QuestionImportBatchViewSet, basename="question-import")

urlpatterns = router.urls
