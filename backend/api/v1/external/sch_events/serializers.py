from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.fields import CharField, EmailField, URLField
from rest_framework.serializers import ModelSerializer

from api.v1.requests.utilities import create_user
from video_requests.models import Request
from video_requests.services import create_request


class RequestExternalSchEventsCreateSerializer(ModelSerializer):
    callback_url = URLField()
    comment = CharField(allow_blank=True, required=False)
    comment_text = CharField(
        allow_blank=True, required=False
    )  # TODO: Backwards compatibility. Remove later.
    requester_email = EmailField()
    requester_first_name = CharField()
    requester_last_name = CharField()
    requester_mobile = PhoneNumberField()

    class Meta:
        model = Request
        fields = (
            "callback_url",
            "comment",
            "comment_text",  # TODO: Backwards compatibility. Remove later.
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
        comment = validated_data.pop(
            "comment", validated_data.pop("comment_text", None)
        )  # TODO: Backwards compatibility. Remove comment_text part later.
        callback_url = validated_data.pop("callback_url")
        requester, additional_data = create_user(validated_data)
        additional_data["external"] = {"sch_events_callback_url": callback_url}
        return create_request(
            additional_data=additional_data,
            comment=comment,
            requested_by=self.context["request"].user,
            requester=requester,
            **validated_data,
        )
