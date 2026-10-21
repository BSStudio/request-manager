from django.db.models import Count, Max, Min, Prefetch
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.viewsets import ModelViewSet

from api.v1.admin.projects.serializers import (
    ProjectAdminListSerializer,
    ProjectAdminRetrieveSerializer,
    ProjectAdminWriteSerializer,
)
from common.rest_framework.permissions import IsStaffUser
from video_requests.models import Project, Request
from video_requests.services import delete_project


class ProjectAdminViewSet(ModelViewSet):
    pagination_class = None
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        if self.action == "list":
            return (
                Project.objects.select_related("responsible")
                .annotate(
                    request_count=Count("requests"),
                    first_start=Min("requests__start_datetime"),
                    last_end=Max("requests__end_datetime"),
                )
                .order_by(Coalesce("last_end", "created").desc(), "-id")
            )
        return Project.objects.select_related("responsible").prefetch_related(
            Prefetch(
                "requests", queryset=Request.objects.order_by("start_datetime", "id")
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectAdminListSerializer
        if self.action == "retrieve":
            return ProjectAdminRetrieveSerializer
        return ProjectAdminWriteSerializer

    @extend_schema(
        request=ProjectAdminWriteSerializer,
        responses=ProjectAdminRetrieveSerializer,
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return Response(self.get_saved_data(project), status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        delete_project(self.get_object())
        return Response(status=HTTP_204_NO_CONTENT)

    def get_saved_data(self, project):
        # Loaded anew: the save changed the requests after they were fetched.
        project = self.get_queryset().get(pk=project.pk)
        return ProjectAdminRetrieveSerializer(
            project, context=self.get_serializer_context()
        ).data

    @extend_schema(
        request=ProjectAdminWriteSerializer,
        responses=ProjectAdminRetrieveSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        request=ProjectAdminWriteSerializer,
        responses=ProjectAdminRetrieveSerializer,
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return Response(self.get_saved_data(project))
