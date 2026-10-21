from django.db.models import Count, Max, Min, Prefetch
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.viewsets import ModelViewSet

from api.v1.admin.projects.serializers import (
    ProjectAdminListSerializer,
    ProjectAdminRetrieveSerializer,
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
        return ProjectAdminRetrieveSerializer

    def destroy(self, request, *args, **kwargs):
        delete_project(self.get_object())
        return Response(status=HTTP_204_NO_CONTENT)
