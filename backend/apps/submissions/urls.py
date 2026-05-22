from rest_framework.routers import DefaultRouter

from apps.submissions.views import SubmissionViewSet

app_name = "submissions"

router = DefaultRouter()
router.register("", SubmissionViewSet, basename="submission")

urlpatterns = router.urls
