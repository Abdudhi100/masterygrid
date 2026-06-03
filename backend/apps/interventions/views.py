from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.models import User
from apps.audit.services import record_audit_log
from apps.common.choices import UserRole
from apps.interventions.models import InterventionNote, StudentIntervention
from apps.interventions.permissions import InterventionPermission
from apps.interventions.selectors import (
    get_interventions_for_user,
    is_platform_admin,
    user_can_access_student,
)
from apps.interventions.serializers import (
    CreateFromProgressReportSerializer,
    InterventionNoteCreateSerializer,
    InterventionNoteSerializer,
    StudentInterventionDetailSerializer,
    StudentInterventionListSerializer,
    StudentInterventionWriteSerializer,
)
from apps.notifications.services import (
    notify_intervention_created,
    notify_intervention_note_added,
)


class StudentInterventionViewSet(viewsets.ModelViewSet):
    permission_classes = [InterventionPermission]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = get_interventions_for_user(self.request.user)
        params = self.request.query_params

        if params.get("school") and is_platform_admin(self.request.user):
            queryset = queryset.filter(school_id=params["school"])
        if params.get("student"):
            queryset = queryset.filter(student_id=params["student"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("priority"):
            queryset = queryset.filter(priority=params["priority"])
        if params.get("category"):
            queryset = queryset.filter(category=params["category"])
        if params.get("assigned_to"):
            queryset = queryset.filter(assigned_to_id=params["assigned_to"])
        if params.get("created_by"):
            queryset = queryset.filter(created_by_id=params["created_by"])
        if params.get("due_date"):
            queryset = queryset.filter(due_date=params["due_date"])
        if params.get("source_type"):
            queryset = queryset.filter(source_type=params["source_type"])
        if params.get("search"):
            search = params["search"].strip()
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(student__full_name__icontains=search)
                | Q(student__email__icontains=search)
            )

        return queryset.order_by("-updated_at", "-created_at")

    def get_serializer_class(self):
        if self.action in {"create", "partial_update", "update"}:
            return StudentInterventionWriteSerializer
        if self.action == "create_from_progress_report":
            return CreateFromProgressReportSerializer
        if self.action == "add_note":
            return InterventionNoteCreateSerializer
        if self.action == "retrieve":
            return StudentInterventionDetailSerializer
        return StudentInterventionListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        intervention = serializer.save()
        record_audit_log(
            actor=request.user,
            action="intervention_created",
            category="intervention",
            obj=intervention,
            school=intervention.school,
            target_user=intervention.student,
            metadata={
                "priority": intervention.priority,
                "status": intervention.status,
                "category": intervention.category,
                "source_type": intervention.source_type,
            },
            request=request,
        )
        notify_intervention_created(intervention)
        output = StudentInterventionDetailSerializer(
            intervention,
            context=self.get_serializer_context(),
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        intervention = self.get_object()
        serializer = self.get_serializer(
            intervention,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        intervention = serializer.save()
        record_audit_log(
            actor=request.user,
            action="intervention_updated",
            category="intervention",
            obj=intervention,
            school=intervention.school,
            target_user=intervention.student,
            metadata={
                "priority": intervention.priority,
                "status": intervention.status,
                "category": intervention.category,
                "updated_fields": list(request.data.keys()),
            },
            request=request,
        )
        output = StudentInterventionDetailSerializer(
            intervention,
            context=self.get_serializer_context(),
        )
        return Response(output.data)

    @action(detail=True, methods=["post"], url_path="add-note")
    def add_note(self, request, pk=None):
        intervention = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = InterventionNote.objects.create(
            intervention=intervention,
            author=request.user,
            note=serializer.validated_data["note"],
            is_internal=serializer.validated_data.get("is_internal", True),
        )
        record_audit_log(
            actor=request.user,
            action="intervention_note_added",
            category="intervention",
            obj=note,
            school=intervention.school,
            target_user=intervention.student,
            metadata={
                "intervention": intervention.id,
                "is_internal": note.is_internal,
            },
            request=request,
        )
        notify_intervention_note_added(intervention, note)
        output = InterventionNoteSerializer(note, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def notes(self, request, pk=None):
        intervention = self.get_object()
        queryset = intervention.notes.select_related("author")
        serializer = InterventionNoteSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"student/(?P<student_id>\d+)")
    def student(self, request, student_id=None):
        student = User.objects.filter(pk=student_id, role=UserRole.STUDENT).first()
        if not student or not user_can_access_student(request.user, student):
            raise PermissionDenied("You do not have access to this student's interventions.")

        queryset = self.filter_queryset(self.get_queryset().filter(student=student))
        serializer = StudentInterventionListSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="create-from-progress-report",
    )
    def create_from_progress_report(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        intervention = serializer.save()
        record_audit_log(
            actor=request.user,
            action="intervention_created",
            category="intervention",
            obj=intervention,
            school=intervention.school,
            target_user=intervention.student,
            metadata={
                "priority": intervention.priority,
                "status": intervention.status,
                "category": intervention.category,
                "source_type": intervention.source_type,
            },
            request=request,
        )
        notify_intervention_created(intervention)
        output = StudentInterventionDetailSerializer(
            intervention,
            context=self.get_serializer_context(),
        )
        return Response(output.data, status=status.HTTP_201_CREATED)
