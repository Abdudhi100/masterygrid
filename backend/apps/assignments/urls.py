from rest_framework.routers import DefaultRouter

from apps.assignments.views import AssignmentViewSet

app_name = "assignments"

router = DefaultRouter()
router.register("", AssignmentViewSet, basename="assignment")

urlpatterns = router.urls
