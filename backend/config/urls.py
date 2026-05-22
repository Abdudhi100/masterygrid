"""Root URL configuration for MasteryGrid."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/schools/", include("apps.schools.urls")),
    path("api/academics/", include("apps.academics.urls")),
    path("api/question-bank/", include("apps.question_bank.urls")),
    path("api/assignments/", include("apps.assignments.urls")),
    path("api/submissions/", include("apps.submissions.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/ai-generation/", include("apps.ai_generation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

