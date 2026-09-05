from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    IntegerField,
    JSONField,
    SerializerMethodField,
)
from rest_framework.relations import PrimaryKeyRelatedField, RelatedField
from rest_framework.serializers import ModelSerializer, Serializer

from api.v1.admin.requests.helpers import (
    get_or_create_requester_from_data,
    handle_additional_data,
    is_status_by_admin,
)
from api.v1.admin.users.serializers import (
    UserNestedDetailSerializer,
    UserNestedListSerializer,
)
from common.models import User
from common.utilities import create_calendar_event, update_calendar_event
from video_requests.emails import (
    email_crew_request_modified,
    email_user_new_request_confirmation,
)
from video_requests.models import Request, Video
from video_requests.services import create_comment
from video_requests.utilities import recalculate_deadline, update_request_status


@extend_schema_field(UserNestedListSerializer)
class CrewMembersListingField(RelatedField):
    def to_representation(self, value):
        serializer = UserNestedListSerializer(value.member)
        return serializer.data


class RequestAdminListSerializer(Serializer):
    created = DateTimeField(read_only=True)
    crew = CrewMembersListingField(many=True, read_only=True)
    deadline = DateField(read_only=True)
    id = IntegerField(read_only=True)
    start_datetime = DateTimeField(read_only=True)
    status = IntegerField(read_only=True)
    status_by_admin = SerializerMethodField(read_only=True)
    responsible = UserNestedListSerializer(read_only=True)
    title = CharField(read_only=True)
    video_count = IntegerField(read_only=True, source="videos.count")

    @staticmethod
    def get_status_by_admin(obj) -> bool:
        return is_status_by_admin(obj)


class RequestAdminRetrieveSerializer(RequestAdminListSerializer):
    additional_data = JSONField(read_only=True)
    comment_count = IntegerField(read_only=True, source="comments.count")
    end_datetime = DateTimeField(read_only=True)
    place = CharField(read_only=True)
    requester = UserNestedDetailSerializer(read_only=True)
    requested_by = UserNestedDetailSerializer(read_only=True)
    responsible = UserNestedDetailSerializer(read_only=True)
    type = CharField(read_only=True)
    videos_edited = SerializerMethodField(read_only=True)

    @staticmethod
    def get_videos_edited(obj) -> bool:
        videos = obj.videos.all()
        return len(videos) > 0 and all(
            video.status >= Video.Statuses.EDITED for video in videos
        )


class RequestAdminUpdateSerializer(ModelSerializer):
    requester = PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    requester_email = EmailField(required=False)
    requester_first_name = CharField(required=False)
    requester_last_name = CharField(required=False)
    requester_mobile = PhoneNumberField(required=False)
    send_notification = BooleanField(required=False)

    class Meta:
        model = Request
        fields = (
            "additional_data",
            "deadline",
            "end_datetime",
            "place",
            "requester",
            "requester_email",
            "requester_first_name",
            "requester_last_name",
            "requester_mobile",
            "responsible",
            "send_notification",
            "start_datetime",
            "title",
            "type",
        )

    field_name_translations = {
        "end_datetime": "Esemény várható befejezése",
        "place": "Helyszín",
        "start_datetime": "Esemény kezdésének ideje",
        "title": "Esemény neve",
        "type": "Videó típusa",
    }

    def get_changed_values(self, instance, validated_data):
        fields_to_check = ["title", "start_datetime", "end_datetime", "place", "type"]
        changed = []
        for field in fields_to_check:
            next_value = validated_data.get(field, None)
            prev_value = getattr(instance, field)
            if next_value and prev_value != next_value:
                changed_field = dict()
                changed_field["name"] = self.field_name_translations[field]
                changed_field["previous"] = prev_value
                changed_field["next"] = next_value
                changed.append(changed_field)
        return changed

    def update(self, instance, validated_data):
        send_notification = validated_data.pop("send_notification", None)
        recalculate_deadline(instance, validated_data)
        handle_additional_data(validated_data, self.context["request"].user, instance)
        if validated_data.get("requester_email"):
            # As validate() should have already run if any of requester attribute exists all should exist.
            get_or_create_requester_from_data(validated_data, instance)
        changed_datetime = now()
        changed_by = self.context["request"].user.get_full_name_eastern_order()
        changed_values = None
        if send_notification:
            changed_values = self.get_changed_values(instance, validated_data)
        request = super().update(instance, validated_data)
        if send_notification and changed_values:
            email_crew_request_modified.delay(
                request.id, changed_by, changed_datetime, changed_values
            )
        update_request_status(request)
        update_calendar_event.delay(request.id)
        return request

    def validate(self, attrs):
        requester_data = [
            attrs.get("requester_email"),
            attrs.get("requester_first_name"),
            attrs.get("requester_last_name"),
            attrs.get("requester_mobile"),
        ]

        if any(requester_data) and attrs.get("requester"):
            raise ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "Either define the requester by its id or its details but not both."
                        )
                    ]
                }
            )

        if any(requester_data) and not all(requester_data):
            raise ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "All requester data fields must be present if one is present."
                        )
                    ]
                }
            )

        return attrs


class RequestAdminCreateSerializer(RequestAdminUpdateSerializer):
    comment = CharField(allow_blank=True, required=False)

    class Meta:
        model = Request
        fields = (
            "additional_data",
            "comment",
            "deadline",
            "end_datetime",
            "place",
            "requester",
            "requester_email",
            "requester_first_name",
            "requester_last_name",
            "requester_mobile",
            "responsible",
            "send_notification",
            "start_datetime",
            "title",
            "type",
        )

    def create(self, validated_data):
        comment_text = validated_data.pop("comment", None)
        send_notification = validated_data.pop("send_notification", None)
        handle_additional_data(validated_data, self.context["request"].user)
        if validated_data.get("requester_email"):
            # As validate() should have already run if any of requester attribute exists all should exist.
            get_or_create_requester_from_data(validated_data)
        if not validated_data.get("requester"):
            validated_data["requester"] = self.context["request"].user
        request = super().create(validated_data)
        if comment_text:
            create_comment(
                author=self.context["request"].user, text=comment_text, request=request
            )
        if send_notification:
            email_user_new_request_confirmation.delay(request.id)
        update_request_status(request)
        create_calendar_event.delay(request.id)
        return request
