from django.db.models import Prefetch
from django.db.models.fields.json import KeyTransform
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ModelViewSet

from api.v1.admin.helpers import serialize_history
from api.v1.admin.requests.filters import VideoFilter
from api.v1.admin.requests.videos.serializers import (
    VideoAdminCreateUpdateSerializer,
    VideoAdminListSerializer,
    VideoAdminRetrieveSerializer,
    VideoAdminSearchSerializer,
)
from api.v1.admin.serializers import HistorySerializer
from common.rest_framework.pagination import ExtendedPagination
from common.rest_framework.permissions import IsStaffUser
from video_requests.models import Rating, Request, Video


class VideoAdminViewSet(ModelViewSet):
    filter_backends = [OrderingFilter]
    ordering = ["title"]
    ordering_fields = [
        "avg_rating",
        "editor__first_name",
        "editor__last_name",
        "status",
        "title",
    ]
    permission_classes = [IsStaffUser]

    @extend_schema(
        request=VideoAdminCreateUpdateSerializer,
        responses=VideoAdminRetrieveSerializer,
    )
    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        self.perform_create(input_serializer)
        output_serializer = VideoAdminRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=HTTP_201_CREATED, headers=headers
        )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Video.objects.none()
        return (
            Video.objects.select_related("editor")
            .prefetch_related(
                Prefetch(
                    "ratings",
                    queryset=Rating.objects.filter(author=self.request.user),
                    to_attr="user_ratings",
                )
            )
            .filter(request=get_object_or_404(Request, pk=self.kwargs["request_pk"]))
        )

    def get_serializer_class(self):
        if self.action == "list":
            return VideoAdminListSerializer
        if self.action == "retrieve":
            return VideoAdminRetrieveSerializer
        return VideoAdminCreateUpdateSerializer

    @extend_schema(
        request=VideoAdminCreateUpdateSerializer,
        responses=VideoAdminRetrieveSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
        )

    @extend_schema(
        request=VideoAdminCreateUpdateSerializer,
        responses=VideoAdminRetrieveSerializer,
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

        output_serializer = VideoAdminRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )

        return Response(output_serializer.data)

    @extend_schema(responses=HistorySerializer(many=True))
    @action(detail=True, filter_backends=[], pagination_class=None)
    def history(self, request, pk=None, request_pk=None):
        history_objects = (
            get_object_or_404(Video, pk=pk, request__pk=request_pk)
            .history.all()
            .order_by("-history_date")
        )
        return Response(serialize_history(history_objects))


class VideoAdminSearchListAPIView(ListAPIView):
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filterset_class = VideoFilter
    ordering = ["-request__start_datetime"]
    ordering_fields = [
        "avg_rating",
        "last_aired",
        "length",
        "request__start_datetime",
        "status",
        "title",
    ]
    pagination_class = ExtendedPagination
    permission_classes = [IsStaffUser]
    search_fields = ["title"]
    serializer_class = VideoAdminSearchSerializer

    def get_queryset(self):
        return (
            Video.objects.select_related("request")
            .prefetch_related("ratings")
            .annotate(
                last_aired=KeyTransform(0, KeyTransform("aired", "additional_data"))
            )
            .annotate(length=KeyTransform("length", "additional_data"))
        )
