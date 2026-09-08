from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.v1.admin.helpers import serialize_history
from api.v1.admin.requests.ratings.serializers import (
    RatingAdminCreateUpdateSerializer,
    RatingAdminListRetrieveSerializer,
)
from api.v1.admin.serializers import HistorySerializer
from common.rest_framework.permissions import IsStaffSelfOrAdmin, IsStaffUser
from video_requests.models import Rating, Request, Video


class RatingAdminViewSet(ModelViewSet):
    filter_backends = [OrderingFilter]
    ordering = ["created"]
    ordering_fields = [
        "author__first_name",
        "author__last_name",
        "created",
        "rating",
        "review",
    ]

    def get_permissions(self):
        # Staff members can read every comment but can only modify and delete those which were created by them.
        if self.request.method in ["GET", "POST"]:
            return [IsStaffUser()]
        return [IsStaffSelfOrAdmin()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Rating.objects.none()
        return Rating.objects.select_related("author").filter(
            video=get_object_or_404(Video, pk=self.kwargs["video_pk"]),
            video__request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RatingAdminListRetrieveSerializer
        return RatingAdminCreateUpdateSerializer

    def perform_create(self, serializer):
        video = get_object_or_404(
            Video,
            pk=self.kwargs["video_pk"],
            request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
        )

        if video.status < Video.Statuses.EDITED:
            # A video cannot be rated before being edited (reached status 3).
            raise ValidationError(
                {"non_field_errors": [_("The video has not been edited yet.")]}
            )

        if Rating.objects.filter(author=self.request.user, video=video).exists():
            # Only one rating per user is permitted for a video.
            raise ValidationError(
                {"non_field_errors": [_("You have already posted a rating.")]}
            )

        serializer.save(author=self.request.user, video=video)

    @extend_schema(responses=HistorySerializer(many=True))
    @action(detail=True, filter_backends=[], pagination_class=None)
    def history(self, request, pk=None, request_pk=None, video_pk=None):
        history_objects = (
            get_object_or_404(
                Rating, pk=pk, video__pk=video_pk, video__request__pk=request_pk
            )
            .history.all()
            .order_by("-history_date")
        )
        return Response(serialize_history(history_objects))

    @extend_schema(responses=RatingAdminListRetrieveSerializer())
    @action(detail=False, filter_backends=[], pagination_class=None)
    def own(self, request, request_pk=None, video_pk=None):
        rating = get_object_or_404(
            Rating,
            author=request.user,
            video__pk=video_pk,
            video__request__pk=request_pk,
        )
        serializer = RatingAdminListRetrieveSerializer(rating)
        return Response(serializer.data)
