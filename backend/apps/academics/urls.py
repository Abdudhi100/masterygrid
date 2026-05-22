from rest_framework.routers import DefaultRouter

from apps.academics.views import (
    AcademicSessionViewSet,
    ClassArmViewSet,
    ClassLevelViewSet,
    LessonLogViewSet,
    StudentEnrollmentViewSet,
    SubjectViewSet,
    TeacherClassSubjectAssignmentViewSet,
    TermViewSet,
    TopicViewSet,
)

app_name = "academics"

router = DefaultRouter()
router.register("academic-sessions", AcademicSessionViewSet, basename="academic-session")
router.register("terms", TermViewSet, basename="term")
router.register("class-levels", ClassLevelViewSet, basename="class-level")
router.register("class-arms", ClassArmViewSet, basename="class-arm")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("topics", TopicViewSet, basename="topic")
router.register(
    "teacher-assignments",
    TeacherClassSubjectAssignmentViewSet,
    basename="teacher-assignment",
)
router.register(
    "student-enrollments",
    StudentEnrollmentViewSet,
    basename="student-enrollment",
)
router.register("lesson-logs", LessonLogViewSet, basename="lesson-log")

urlpatterns = router.urls
