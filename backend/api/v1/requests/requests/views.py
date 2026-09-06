from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.v1.requests.requests.serializers import (
    RequestAnonymousCreateSerializer,
    RequestCreateSerializer,
    RequestListSerializer,
    RequestRetrieveSerializer,
)
from common.rest_framework.pagination import ExtendedPagination
from common.rest_framework.permissions import IsSelf
from video_requests.models import Request


class RequestViewSet(CreateModelMixin, ReadOnlyModelViewSet):
    filter_backends = [
        OrderingFilter,
        SearchFilter,
    ]
    ordering = ["created"]
    ordering_fields = [
        "created",
        "start_datetime",
        "status",
        "title",
    ]
    pagination_class = ExtendedPagination
    search_fields = ["title", "videos__title"]

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name="",
            resource_type_field_name=None,
            serializers=[
                RequestCreateSerializer,
                RequestAnonymousCreateSerializer,
            ],
        ),
        responses=RequestRetrieveSerializer,
    )
    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        self.perform_create(input_serializer)
        output_serializer = RequestRetrieveSerializer(
            input_serializer.instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data, status=HTTP_201_CREATED, headers=headers
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsSelf()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Request.objects.none()

        if self.action == "list":
            return Request.objects.filter(requester=self.request.user)

        return (
            Request.objects.select_related("requester")
            .select_related("requested_by")
            .select_related("responsible")
            .filter(requester=self.request.user)
        )

    def get_serializer_class(self):
        if self.action == "list":
            return RequestListSerializer
        if self.action == "retrieve":
            return RequestRetrieveSerializer
        if not self.request.user.is_anonymous:
            return RequestCreateSerializer
        return RequestAnonymousCreateSerializer
