from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import iri_to_uri
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.viewsets import GenericViewSet
from social_core.exceptions import AuthException

from api.v1.admin.users.serializers import UserAdminWorkedOnSerializer
from api.v1.admin.users.views import UserAdminViewSet
from api.v1.me.serializers import OAuth2ConnectSerializer, UserSerializer
from common.models import User
from common.rest_framework.permissions import IsAuthenticated, IsStaffUser
from common.social_core.helpers import decorate_request, handle_exception


class MeViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return User.objects.get(pk=self.request.user.pk)

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
    @action(
        detail=True,
        filter_backends=[],
        pagination_class=None,
        permission_classes=[IsStaffUser],
    )
    def worked_on(self, request, pk=None):
        return UserAdminViewSet.worked_on(UserAdminViewSet(), request, request.user.pk)


class OAuth2ConnectDisconnectView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OAuth2ConnectSerializer

    @staticmethod
    def validate_provider(provider):
        if provider not in settings.SOCIAL_AUTH_PROVIDERS:
            raise ValidationError({"provider": _("Invalid provider.")})
        return provider

    def delete(self, request, *args, **kwargs):
        provider = self.validate_provider(self.kwargs.get("provider"))
        decorate_request(request, provider)
        request.backend.disconnect(user=self.request.user)
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        request=OAuth2ConnectSerializer,
        responses={HTTP_201_CREATED: {}},
    )
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = self.validate_provider(self.kwargs.get("provider"))

        decorate_request(request, provider)

        origin = self.request.strategy.request.META.get("HTTP_ORIGIN")
        if origin:
            relative_path = urlparse(self.request.backend.redirect_uri).path
            url = urlparse(origin)
            origin_scheme_host = f"{url.scheme}://{url.netloc}"
            location = urljoin(origin_scheme_host, relative_path)
            self.request.backend.redirect_uri = iri_to_uri(location)

        try:
            request.backend.REDIRECT_STATE = False
            request.backend.STATE_PARAMETER = False

            user = request.backend.complete(user=self.request.user)

            if isinstance(user, HttpResponse):
                # error happened and pipeline returned HttpResponse instead of user
                # the object is still named user but it's an HttpResponse object containing error
                raise AuthException(provider, user)
        except Exception as e:
            message = handle_exception(e)
            return Response(data=message, status=HTTP_400_BAD_REQUEST)

        return Response(status=HTTP_201_CREATED)
