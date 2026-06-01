from rest_framework.routers import DefaultRouter

from apps.interventions.views import StudentInterventionViewSet

app_name = "interventions"

router = DefaultRouter()
router.register("", StudentInterventionViewSet, basename="intervention")

urlpatterns = router.urls
