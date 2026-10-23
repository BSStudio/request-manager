from urllib.parse import urlparse

from django.utils.translation import gettext_lazy as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField,
    ChoiceField,
    EmailField,
    IntegerField,
    URLField,
)
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer, Serializer
from social_django.models import UserSocialAuth

from common.models import User
from video_requests.models import Notification


class OAuth2ConnectSerializer(Serializer):
    code = CharField()
    nonce = CharField()


class UserSocialAuthSerializer(ModelSerializer):
    class Meta:
        model = UserSocialAuth
        fields = ("provider", "uid")
        read_only_fields = ("provider", "uid")


class UserSerializer(ModelSerializer):
    AVATAR_PROVIDER_CHOICES = (
        ("bss-login", "BSS"),
        ("google-oauth2", "Google"),
        ("gravatar", "Gravatar"),
        ("microsoft-graph", "Microsoft"),
    )

    avatar_provider = ChoiceField(
        choices=AVATAR_PROVIDER_CHOICES,
        required=False,
        write_only=True,
    )
    email = EmailField(required=False)
    first_name = CharField(max_length=150, required=False)
    groups = SlugRelatedField(many=True, read_only=True, slug_field="name")
    last_name = CharField(max_length=150, required=False)
    phone_number = PhoneNumberField(required=False)
    role = CharField(read_only=True)
    social_accounts = UserSocialAuthSerializer(
        many=True, read_only=True, source="social_auth"
    )

    class Meta:
        model = User
        fields = (
            "avatar",
            "avatar_provider",
            "avatar_url",
            "email",
            "first_name",
            "groups",
            "id",
            "last_name",
            "phone_number",
            "role",
            "social_accounts",
            "username",
        )
        read_only_fields = (
            "avatar",
            "avatar_url",
            "groups",
            "id",
            "role",
            "social_accounts",
            "username",
        )

    def update(self, instance, validated_data):
        email = validated_data.get("email")
        if (
            email
            and User.objects.filter(email__iexact=email)
            .exclude(pk=instance.pk)
            .exists()
        ):
            raise ValidationError({"email": [_("E-mail address already in use.")]})
        avatar_provider = validated_data.pop("avatar_provider", None)
        if avatar_provider:
            instance.avatar["provider"] = avatar_provider
        return super().update(instance, validated_data)


class NotificationSerializer(ModelSerializer):
    title = CharField(read_only=True)
    url = CharField(read_only=True)

    class Meta:
        model = Notification
        fields = ("body", "created", "id", "kind", "read_at", "request", "title", "url")
        read_only_fields = fields


class UnreadCountSerializer(Serializer):
    count = IntegerField()


class MarkNotificationsReadSerializer(Serializer):
    request = IntegerField(required=False)


# The push services of the browsers we support. Any other endpoint would make
# the server send requests wherever a user points it, internal hosts included.
PUSH_SERVICE_HOSTS = (
    "fcm.googleapis.com",
    "notify.windows.com",
    "push.apple.com",
    "push.services.mozilla.com",
)


class PushSubscriptionKeysSerializer(Serializer):
    auth = CharField(max_length=100)
    p256dh = CharField(max_length=200)


class PushSubscriptionSerializer(Serializer):
    endpoint = URLField(max_length=1000)
    keys = PushSubscriptionKeysSerializer()

    def validate_endpoint(self, endpoint):
        url = urlparse(endpoint)
        host = url.hostname or ""
        # Only a bare host, as browsers send it: requests splits a URL with a
        # backslash differently and would connect to another host.
        if (
            url.scheme != "https"
            or "\\" in endpoint
            or url.netloc != host
            or not any(
                host == service or host.endswith(f".{service}")
                for service in PUSH_SERVICE_HOSTS
            )
        ):
            raise ValidationError(_("Unsupported push service."))
        return endpoint


class PushSubscriptionRemoveSerializer(Serializer):
    endpoint = URLField(max_length=1000)


class VapidPublicKeySerializer(Serializer):
    public_key = CharField()
