from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet

from api.v1.admin.requests.filters import TodoFilter
from api.v1.admin.todos.serializers import (
    TodoAdminCreateUpdateSerializer,
    TodoAdminListRetrieveSerializer,
)
from common.models import User
from common.rest_framework.pagination import ExtendedPagination
from common.rest_framework.permissions import IsStaffSelfOrAdmin, IsStaffUser
from video_requests.models import Request, Todo, Video


class TodoAdminViewSet(RetrieveUpdateDestroyAPIView, ListModelMixin, GenericViewSet):
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]
    filterset_class = TodoFilter
    ordering = ["created"]
    ordering_fields = [
        "created",
        "status",
    ]
    pagination_class = ExtendedPagination
    queryset = (
        Todo.objects.select_related("creator__userprofile")
        .select_related("request")
        .select_related("video")
        .prefetch_related(
            Prefetch(
                "assignees",
                queryset=User.objects.select_related("userprofile"),
            ),
        )
        .all()
    )

    def get_permissions(self):
        # Staff members can only delete Todos created by them.
        if self.request.method in ["DELETE"]:
            return [IsStaffSelfOrAdmin()]
        return [IsStaffUser()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TodoAdminListRetrieveSerializer
        return TodoAdminCreateUpdateSerializer

    @extend_schema(
        request=TodoAdminCreateUpdateSerializer,
        responses=TodoAdminListRetrieveSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        request=TodoAdminCreateUpdateSerializer,
        responses=TodoAdminListRetrieveSerializer,
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

        output_serializer = TodoAdminListRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )

        return Response(output_serializer.data)


class TodoAdminRequestVideoViewSet(ListCreateAPIView, GenericViewSet):
    filter_backends = [OrderingFilter]
    ordering = ["created"]
    ordering_fields = [
        "created",
        "status",
    ]
    permission_classes = [IsStaffUser]

    @extend_schema(
        request=TodoAdminCreateUpdateSerializer,
        responses=TodoAdminListRetrieveSerializer,
    )
    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        self.perform_create(input_serializer)
        output_serializer = TodoAdminListRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=HTTP_201_CREATED, headers=headers
        )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Todo.objects.none()
        if self.kwargs.get("video_pk"):
            return (
                Todo.objects.select_related("creator__userprofile")
                .select_related("request")
                .select_related("video")
                .prefetch_related(
                    Prefetch(
                        "assignees",
                        queryset=User.objects.select_related("userprofile"),
                    )
                )
                .filter(
                    request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
                    video=get_object_or_404(Video, pk=self.kwargs["video_pk"]),
                )
            )
        return (
            Todo.objects.select_related("creator__userprofile")
            .select_related("request")
            .select_related("video")
            .prefetch_related(
                Prefetch(
                    "assignees",
                    queryset=User.objects.select_related("userprofile"),
                )
            )
            .filter(
                request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
            )
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TodoAdminListRetrieveSerializer
        return TodoAdminCreateUpdateSerializer

    def perform_create(self, serializer):
        request = get_object_or_404(Request, pk=self.kwargs["request_pk"])
        if self.kwargs.get("video_pk"):
            video = get_object_or_404(
                Video,
                pk=self.kwargs["video_pk"],
                request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
            )
            serializer.save(creator=self.request.user, request=request, video=video)
        serializer.save(creator=self.request.user, request=request)
