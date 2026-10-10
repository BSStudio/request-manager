from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateTimeField, EmailField, IntegerField
from rest_framework.serializers import ModelSerializer, Serializer

from api.v1.admin.users.serializers import (
    UserNestedDetailSerializer,
    UserNestedListSerializer,
)
from api.v1.requests.utilities import create_user
from common.models import get_anonymous_user
from common.rest_framework.turnstile import TurnstileField
from video_requests.models import Request
from video_requests.services import create_request


class RequestListSerializer(Serializer):
    created = DateTimeField(read_only=True)
    id = IntegerField(read_only=True)
    start_datetime = DateTimeField(read_only=True)
    status = IntegerField(read_only=True)
    title = CharField(read_only=True)


class RequestRetrieveSerializer(RequestListSerializer):
    end_datetime = DateTimeField(read_only=True)
    place = CharField(read_only=True)
    requester = UserNestedDetailSerializer(read_only=True)
    requested_by = UserNestedListSerializer(read_only=True)
    responsible = UserNestedDetailSerializer(read_only=True)
    type = CharField(read_only=True)


class RequestCreateSerializer(ModelSerializer):
    comment = CharField(allow_blank=True, required=False)

    class Meta:
        model = Request
        fields = (
            "comment",
            "end_datetime",
            "place",
            "start_datetime",
            "title",
            "type",
        )

    def create(self, validated_data):
        user = self.context["request"].user
        comment = validated_data.pop("comment", None)
        return create_request(
            comment=comment, requested_by=user, requester=user, **validated_data
        )

    def validate(self, attrs):
        if attrs.get("start_datetime") < localtime():
            raise ValidationError(
                {"start_datetime": _("Must be later than current time.")}
            )
        user = self.context["request"].user
        if not user.is_anonymous and not all(
            [user.email, user.first_name, user.last_name, user.phone_number]
        ):
            raise ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "Please fill all data in your profile before sending a request."
                        )
                    ]
                }
            )
        return attrs


class RequestAnonymousCreateSerializer(RequestCreateSerializer):
    captcha = TurnstileField()
    requester_email = EmailField()
    requester_first_name = CharField()
    requester_last_name = CharField()
    requester_mobile = PhoneNumberField()

    class Meta:
        model = Request
        fields = (
            "captcha",
            "comment",
            "end_datetime",
            "place",
            "requester_first_name",
            "requester_email",
            "requester_last_name",
            "requester_mobile",
            "start_datetime",
            "title",
            "type",
        )

    def create(self, validated_data):
        comment = validated_data.pop("comment", None)
        requester, additional_data = create_user(validated_data)
        return create_request(
            additional_data=additional_data,
            comment=comment,
            requested_by=get_anonymous_user(),
            requester=requester,
            **validated_data,
        )

    def validate(self, attrs):
        attrs.pop("captcha", None)
        return super().validate(attrs)
