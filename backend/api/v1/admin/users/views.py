from datetime import date, timedelta

from decouple import strtobool
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet

from api.v1.admin.users.filters import UserFilter
from api.v1.admin.users.serializers import (
    BanUserSerializer,
    UserAdminListSerializer,
    UserAdminRetrieveUpdateSerializer,
    UserAdminWorkedOnSerializer,
)
from common.models import Ban, User
from common.rest_framework.pagination import ExtendedPagination
from common.rest_framework.permissions import (
    IsAdminUser,
    IsStaffSelfOrAdmin,
    IsStaffUser,
)
from video_requests.models import CrewMember, Request, Video


class UserAdminViewSet(
    RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet
):
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    filterset_class = UserFilter
    ordering = ["full_name"]
    ordering_fields = [
        "email",
        "full_name",
        "is_staff",
        "phone_number",
    ]
    pagination_class = ExtendedPagination
    queryset = (
        User.objects.prefetch_related("groups")
        .annotate(full_name=Concat("last_name", Value(" "), "first_name"))
        .all()
        .cache()
    )
    search_fields = ["first_name", "last_name"]

    def get_permissions(self):
        if self.action.endswith("ban"):
            return [IsAdminUser()]
        if "update" in self.action:
            return [IsStaffSelfOrAdmin()]
        return [IsStaffUser()]

    def get_serializer_class(self):
        if self.action == "list":
            return UserAdminListSerializer
        return UserAdminRetrieveUpdateSerializer

    @extend_schema(request=BanUserSerializer, responses=BanUserSerializer)
    @action(detail=True, filter_backends=[], methods=["post"], pagination_class=None)
    def ban(self, request, pk=None):
        serializer = BanUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            creator=self.request.user,
            receiver=get_object_or_404(User, pk=pk),
        )
        return Response(serializer.data, status=HTTP_201_CREATED)

    @extend_schema()
    @ban.mapping.delete
    def delete_ban(self, request, pk=None):
        instance = get_object_or_404(Ban, receiver__pk=pk)
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_responsible",
                OpenApiTypes.BOOL,
                OpenApiParameter.QUERY,
                description="Default is True.",
            ),
            OpenApiParameter(
                "start_datetime_after",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Default is 20 weeks before start_datetime_before.",
            ),
            OpenApiParameter(
                "start_datetime_before",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Default is today.",
            ),
        ],
        responses=UserAdminWorkedOnSerializer(many=True),
    )
    @action(detail=True, filter_backends=[], pagination_class=None)
    def worked_on(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        worked_on = []

        # Get and validate all query parameters by trying to convert them to the corresponding type
        # if not the default value was used.
        try:
            start_datetime_before = request.query_params.get(
                "start_datetime_before", localdate()
            )
            start_datetime_before = (
                date.fromisoformat(start_datetime_before)
                if type(start_datetime_before) is str
                else start_datetime_before
            )
        except ValueError:
            raise ValidationError({"start_datetime_before": [_("Invalid filter.")]})

        try:
            start_datetime_after = request.query_params.get(
                "start_datetime_after", start_datetime_before - timedelta(weeks=20)
            )
            start_datetime_after = (
                date.fromisoformat(start_datetime_after)
                if type(start_datetime_after) is str
                else start_datetime_after
            )
        except ValueError:
            raise ValidationError({"start_datetime_after": [_("Invalid filter.")]})

        try:
            is_responsible = request.query_params.get("is_responsible", True)
            is_responsible = (
                strtobool(is_responsible)
                if type(is_responsible) is str
                else is_responsible
            )
        except ValueError:
            raise ValidationError({"is_responsible": [_("Invalid filter.")]})

        # Check if date range is valid
        if start_datetime_before < start_datetime_after:
            raise ValidationError(
                {
                    "start_datetime_after": [
                        _("Must be earlier than start_datetime_before.")
                    ]
                }
            )

        date_range = [start_datetime_after, start_datetime_before]

        if is_responsible:
            for req in Request.objects.filter(
                responsible=user,
                start_datetime__date__range=date_range,
            ):
                worked_on.append(
                    {
                        "id": req.id,
                        "title": req.title,
                        "start_datetime": req.start_datetime,
                        "position": _("Responsible"),
                    }
                )

        for crew in CrewMember.objects.select_related("request").filter(
            member=user,
            request__start_datetime__date__range=date_range,
        ):
            worked_on.append(
                {
                    "id": crew.request.id,
                    "title": crew.request.title,
                    "start_datetime": crew.request.start_datetime,
                    "position": crew.position,
                }
            )

        for video in Video.objects.select_related("request").filter(
            editor=user,
            request__start_datetime__date__range=date_range,
        ):
            worked_on.append(
                {
                    "id": video.request.id,
                    "title": video.request.title,
                    "start_datetime": video.request.start_datetime,
                    "position": _("Editor"),
                }
            )

        serializer = UserAdminWorkedOnSerializer(worked_on, many=True)
        return Response(serializer.data)
