import hashlib
import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.generics import CreateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from api.v1.external.sch_events.serializers import (
    RequestExternalSchEventsCreateSerializer,
)
from api.v1.requests.comments.serializers import CommentCreateUpdateSerializer
from api.v1.requests.requests.serializers import RequestRetrieveSerializer
from common.rest_framework.exception import exception_handler
from common.rest_framework.permissions import IsServiceAccount
from video_requests.models import Request

logger = logging.getLogger(__name__)

BAD_REQUEST_REPORT_INTERVAL = 60 * 60 * 24


def external_api_exception_handler(exc, context):
    if isinstance(exc, (ValidationError, ParseError)):
        request = context["request"]
        path = request.get_full_path()
        # Sentry records only errors, and bejelentes.sch retries a rejected
        # request every few minutes: each body is an error once a day.
        first = cache.add(
            f"sch-events-bad-request:{path}:{hashlib.sha256(request.body).hexdigest()}",
            True,
            timeout=BAD_REQUEST_REPORT_INTERVAL,
        )
        logger.log(
            logging.ERROR if first else logging.WARNING,
            "SCH Events (bejelentes.sch) bad request: %s %s body=%s",
            request.method,
            path,
            request.body.decode(errors="backslashreplace"),
            exc_info=True,
        )
    return exception_handler(exc, context)


class ExternalSchEventsBadRequestMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Django keeps the raw body only if it is read before DRF parses the stream.
        request.body

    def get_exception_handler(self):
        return external_api_exception_handler


@extend_schema(
    request=RequestExternalSchEventsCreateSerializer,
    responses=RequestRetrieveSerializer,
)
class RequestExternalSchEventsCreateView(
    ExternalSchEventsBadRequestMixin, CreateAPIView
):
    permission_classes = [IsServiceAccount]
    serializer_class = RequestExternalSchEventsCreateSerializer

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


class RequestExternalSchEventsRetrieveView(RetrieveAPIView):
    permission_classes = [IsServiceAccount]
    serializer_class = RequestRetrieveSerializer

    def get_queryset(self):
        return Request.objects.filter(requested_by=self.request.user)


class CommentExternalSchEventsCreateView(
    ExternalSchEventsBadRequestMixin, generics.CreateAPIView
):
    permission_classes = [IsServiceAccount]
    serializer_class = CommentCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            request=get_object_or_404(
                Request, pk=self.kwargs["request_pk"], requested_by=self.request.user
            ),
        )
