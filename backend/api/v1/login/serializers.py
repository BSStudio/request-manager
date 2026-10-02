from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import iri_to_uri
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import (
    TokenBlacklistSerializer as SimpleJWTTokenBlacklistSerializer,
)
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer as SimpleJWTTokenObtainPairSerializer,
)
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from social_core.exceptions import AuthException

from common.models import User
from common.social_core.helpers import decorate_request


class TokenBlacklistSerializer(SimpleJWTTokenBlacklistSerializer):
    refresh = CharField(required=False, write_only=True)

    def validate(self, attrs):
        if "refresh" not in attrs:
            return {}
        refresh = self.token_class(attrs["refresh"])
        if refresh.payload["user_id"] == str(self.context["request"].user.id):
            refresh.blacklist()
            return {}
        raise NotAuthenticated(detail="Token is invalid or expired")


class TokenObtainPairOAuth2Serializer(SimpleJWTTokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["avatar"] = user.avatar_url
        token["groups"] = list(user.groups.values_list("name", flat=True))
        token["name"] = user.get_full_name_eastern_order()
        token["role"] = user.role
        return token

    # This part is a heavily modified and stripped down
    # version of https://github.com/st4lk/django-rest-social-auth

    code = CharField()
    provider = CharField()

    def __init__(self, *args, **kwargs):
        super(TokenObtainSerializer, self).__init__(*args, **kwargs)

    def get_user(self):
        origin = self.context["request"].strategy.request.META.get("HTTP_ORIGIN")
        if origin:
            relative_path = urlparse(self.context["request"].backend.redirect_uri).path
            url = urlparse(origin)
            origin_scheme_host = f"{url.scheme}://{url.netloc}"
            location = urljoin(origin_scheme_host, relative_path)
            self.context["request"].backend.redirect_uri = iri_to_uri(location)

        # skip checking state by setting following params to False
        # it is responsibility of front-end to check state
        self.context["request"].backend.REDIRECT_STATE = False
        self.context["request"].backend.STATE_PARAMETER = False

        user = self.context["request"].backend.complete(request=self.context["request"])
        return user

    def validate(self, attrs):
        if attrs["provider"] not in settings.SOCIAL_AUTH_PROVIDERS:
            raise ValidationError({"provider": _("Invalid provider.")})

        decorate_request(self.context["request"], attrs["provider"])
        user = self.get_user()

        if isinstance(user, HttpResponse):
            # error happened and pipeline returned HttpResponse instead of user
            # the object is still named user, but it's an HttpResponse object containing error
            raise AuthException(attrs["provider"], user)

        refresh = self.get_token(user)

        return {
            "user": user,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class SessionUserSerializer(ModelSerializer):
    avatar_url = CharField(allow_null=True, read_only=True)
    groups = SlugRelatedField(many=True, read_only=True, slug_field="name")
    name = CharField(source="get_full_name_eastern_order", read_only=True)
    role = CharField(read_only=True)

    class Meta:
        model = User
        fields = ("avatar_url", "groups", "id", "name", "role")


class LoginResponseSerializer(SessionUserSerializer):
    access = SerializerMethodField()
    refresh = SerializerMethodField()

    class Meta(SessionUserSerializer.Meta):
        fields = (*SessionUserSerializer.Meta.fields, "access", "refresh")

    def get_access(self, obj) -> str:
        return self.context["access"]

    def get_refresh(self, obj) -> str:
        return self.context["refresh"]
