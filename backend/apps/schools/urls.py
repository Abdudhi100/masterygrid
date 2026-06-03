from django.urls import path

from apps.schools.views import SchoolSetupStatusAPIView

app_name = "schools"

urlpatterns = [
    path(
        "setup-status/",
        SchoolSetupStatusAPIView.as_view(),
        name="setup-status",
    ),
]
