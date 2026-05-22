from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    CurrentUserView,
    RegisterUserView,
    StudentProfileViewSet,
    StudentViewSet,
    TeacherProfileViewSet,
    TeacherViewSet,
)

app_name = "accounts"

router = DefaultRouter()
router.register("teachers", TeacherViewSet, basename="teacher")
router.register("students", StudentViewSet, basename="student")
router.register("teacher-profiles", TeacherProfileViewSet, basename="teacher-profile")
router.register("student-profiles", StudentProfileViewSet, basename="student-profile")

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="me"),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
] + router.urls
