from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.v1.admin.helpers import serialize_history
from api.v1.admin.requests.comments.serializers import (
    CommentAdminCreateUpdateSerializer,
    CommentAdminListRetrieveSerializer,
)
from api.v1.admin.serializers import HistorySerializer
from common.rest_framework.permissions import IsStaffSelfOrAdmin, IsStaffUser
from video_requests.models import Comment, Request


class CommentAdminViewSet(ModelViewSet):
    filter_backends = [OrderingFilter]
    ordering = ["created"]
    ordering_fields = ["author__first_name", "author__last_name", "created", "internal"]

    def get_permissions(self):
        # Staff members can read every comment but can only modify and delete those which were created by them.
        if self.request.method in ["GET", "POST"]:
            return [IsStaffUser()]
        return [IsStaffSelfOrAdmin()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        return Comment.objects.select_related("author").filter(
            request=get_object_or_404(Request, pk=self.kwargs["request_pk"])
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentAdminListRetrieveSerializer
        return CommentAdminCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            request=get_object_or_404(Request, pk=self.kwargs["request_pk"]),
        )

    @extend_schema(responses=HistorySerializer(many=True))
    @action(detail=True, filter_backends=[], pagination_class=None)
    def history(self, request, pk=None, request_pk=None):
        history_objects = (
            get_object_or_404(Comment, pk=pk, request__pk=request_pk)
            .history.all()
            .order_by("-history_date")
        )
        return Response(serialize_history(history_objects))
