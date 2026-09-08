from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet

from api.v1.requests.comments.serializers import (
    CommentCreateUpdateSerializer,
    CommentListRetrieveSerializer,
)
from common.rest_framework.permissions import IsAuthenticated, IsSelf
from video_requests.models import Comment, Request


class CommentViewSet(ModelViewSet):
    filter_backends = [OrderingFilter]
    ordering = ["created"]
    ordering_fields = ["author__first_name", "author__last_name", "created"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        return Comment.objects.select_related("author").filter(
            internal=False,
            request=get_object_or_404(
                Request, pk=self.kwargs["request_pk"], requester=self.request.user
            ),
        )

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsSelf()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentListRetrieveSerializer
        return CommentCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            internal=False,
            request=get_object_or_404(
                Request, pk=self.kwargs["request_pk"], requester=self.request.user
            ),
        )
