from rest_framework.routers import DefaultRouter

from apps.practice.views import PracticeSessionViewSet

app_name = "practice"

router = DefaultRouter()
router.register("sessions", PracticeSessionViewSet, basename="practice-session")

urlpatterns = router.urls
