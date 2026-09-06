from django.db.models import Count, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ModelViewSet

from api.v1.admin.helpers import serialize_history
from api.v1.admin.requests.filters import RequestFilter
from api.v1.admin.requests.requests.serializers import (
    RequestAdminCreateSerializer,
    RequestAdminListSerializer,
    RequestAdminRetrieveSerializer,
    RequestAdminUpdateSerializer,
)
from api.v1.admin.serializers import HistorySerializer
from common.rest_framework.pagination import ExtendedPagination
from common.rest_framework.permissions import IsStaffSelfOrAdmin, IsStaffUser
from common.utilities import remove_calendar_event
from video_requests.models import CrewMember, Request


class RequestAdminViewSet(ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filterset_class = RequestFilter
    ordering = ["created"]
    ordering_fields = [
        "created",
        "deadline",
        "responsible__first_name",
        "responsible__last_name",
        "start_datetime",
        "status",
        "title",
    ]
    pagination_class = ExtendedPagination
    search_fields = ["title"]

    @extend_schema(
        request=RequestAdminCreateSerializer,
        responses=RequestAdminRetrieveSerializer,
    )
    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        self.perform_create(input_serializer)
        output_serializer = RequestAdminRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=HTTP_201_CREATED, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        video_request = get_object_or_404(Request, pk=self.kwargs["pk"])
        remove_calendar_event.delay(video_request.id)
        return super().destroy(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method == "DELETE":
            # Staff members can only delete requests which were created by them.
            return [IsStaffSelfOrAdmin()]
        return [IsStaffUser()]

    def get_queryset(self):
        if self.action == "list":
            return (
                Request.objects.select_related("responsible")
                .prefetch_related(
                    Prefetch(
                        "crew",
                        queryset=CrewMember.objects.select_related("member"),
                    ),
                )
                .annotate(video_count=Count("videos"))
                .cache()
            )

        return (
            Request.objects.select_related("requester")
            .select_related("requested_by")
            .select_related("responsible")
            .prefetch_related(
                Prefetch(
                    "crew",
                    queryset=CrewMember.objects.select_related("member"),
                ),
            )
            .prefetch_related("videos")
            .annotate(comment_count=Count("comments"), video_count=Count("videos"))
        )

    def get_serializer_class(self):
        if self.action == "list":
            return RequestAdminListSerializer
        if self.action == "retrieve":
            return RequestAdminRetrieveSerializer
        if self.action == "update":
            return RequestAdminUpdateSerializer
        return RequestAdminCreateSerializer

    @extend_schema(
        request=RequestAdminUpdateSerializer,
        responses=RequestAdminRetrieveSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @extend_schema(
        request=RequestAdminUpdateSerializer,
        responses=RequestAdminRetrieveSerializer,
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        input_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        input_serializer.is_valid(raise_exception=True)
        self.perform_update(input_serializer)

        instance._prefetched_objects_cache = {}

        output_serializer = RequestAdminRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )

        return Response(output_serializer.data)

    @extend_schema(responses=HistorySerializer(many=True))
    @action(detail=True, filter_backends=[], pagination_class=None)
    def history(self, request, pk=None):
        history_objects = (
            get_object_or_404(Request, pk=pk).history.all().order_by("-history_date")
        )
        return Response(serialize_history(history_objects))
