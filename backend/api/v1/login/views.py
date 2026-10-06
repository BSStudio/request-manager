from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api.v1.login.serializers import (
    SessionUserSerializer,
    SocialLoginSerializer,
)
from common.rest_framework.permissions import IsAuthenticated
from common.social_core.helpers import handle_exception


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response(status=HTTP_204_NO_CONTENT)


class SocialLoginView(GenericAPIView):
    # A leftover session must not block logging in again; login() replaces it.
    authentication_classes = []
    # Cross-site forms cannot send JSON, so they cannot log a victim in.
    parser_classes = [JSONParser]
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        request=SocialLoginSerializer,
        responses=SessionUserSerializer,
    )
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)

        try:
            input_serializer.is_valid(raise_exception=True)
        except Exception as e:
            message = handle_exception(e)
            return Response(data=message, status=HTTP_400_BAD_REQUEST)

        user = input_serializer.validated_data["user"]
        login(request, user)
        return Response(SessionUserSerializer(user).data, status=HTTP_200_OK)
