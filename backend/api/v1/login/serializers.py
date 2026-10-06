from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import iri_to_uri
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer, Serializer
from social_core.exceptions import AuthException

from common.models import User
from common.social_core.helpers import decorate_request


class TokenObtainPairOAuth2Serializer(Serializer):
    # This part is a heavily modified and stripped down
    # version of https://github.com/st4lk/django-rest-social-auth

    code = CharField()
    provider = CharField()

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

        return {"user": user}


class SessionUserSerializer(ModelSerializer):
    avatar_url = CharField(allow_null=True, read_only=True)
    groups = SlugRelatedField(many=True, read_only=True, slug_field="name")
    name = CharField(source="get_full_name_eastern_order", read_only=True)
    role = CharField(read_only=True)

    class Meta:
        model = User
        fields = ("avatar_url", "groups", "id", "name", "role")
