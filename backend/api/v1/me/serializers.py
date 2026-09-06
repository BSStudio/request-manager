from django.utils.translation import gettext_lazy as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, EmailField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer, Serializer
from social_django.models import UserSocialAuth

from common.models import User


class OAuth2ConnectSerializer(Serializer):
    code = CharField()


class UserProfileSerializer(ModelSerializer):
    AVATAR_PROVIDER_CHOICES = (
        ("google-oauth2", "Google"),
        ("gravatar", "Gravatar"),
        ("microsoft-graph", "Microsoft"),
    )

    avatar_provider = ChoiceField(
        choices=AVATAR_PROVIDER_CHOICES,
        required=False,
        write_only=True,
    )
    phone_number = PhoneNumberField(required=False)

    class Meta:
        model = User
        fields = (
            "avatar",
            "avatar_provider",
            "avatar_url",
            "phone_number",
        )
        read_only_fields = ("avatar", "avatar_url")
        write_only_fields = ("avatar_provider",)


class UserSocialAuthSerializer(ModelSerializer):
    class Meta:
        model = UserSocialAuth
        fields = ("provider", "uid")
        read_only_fields = ("provider", "uid")


class UserSerializer(ModelSerializer):
    email = EmailField(required=False)
    first_name = CharField(max_length=150, required=False)
    groups = SlugRelatedField(many=True, read_only=True, slug_field="name")
    last_name = CharField(max_length=150, required=False)
    profile = UserProfileSerializer(source="*")
    role = CharField(read_only=True)
    social_accounts = UserSocialAuthSerializer(
        many=True, read_only=True, source="social_auth"
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "groups",
            "id",
            "last_name",
            "profile",
            "role",
            "social_accounts",
            "username",
        )
        read_only_fields = ("groups", "id", "role", "social_accounts", "username")

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
