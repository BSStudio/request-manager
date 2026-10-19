from rest_framework.fields import (
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    JSONField,
    SerializerMethodField,
)
from rest_framework.serializers import ModelSerializer, Serializer

from api.v1.admin.requests.helpers import handle_additional_data, is_status_by_admin
from api.v1.admin.users.serializers import UserNestedListSerializer
from video_requests.models import Video
from video_requests.utilities import update_video_status


class VideoAdminListSerializer(Serializer):
    avg_rating = FloatField(default=0.0, read_only=True)
    editor = UserNestedListSerializer(read_only=True)
    id = IntegerField(read_only=True)
    rated = SerializerMethodField(read_only=True)
    status = IntegerField(read_only=True)
    status_by_admin = SerializerMethodField(read_only=True)
    title = CharField(read_only=True)

    @staticmethod
    def get_rated(obj) -> bool:
        return len(getattr(obj, "user_ratings", [])) > 0

    @staticmethod
    def get_status_by_admin(obj) -> bool:
        return is_status_by_admin(obj)


class VideoAdminRetrieveSerializer(VideoAdminListSerializer):
    additional_data = JSONField(read_only=True)
    edited_at = DateField(allow_null=True, read_only=True)


class VideoAdminCreateUpdateSerializer(ModelSerializer):
    class Meta:
        model = Video
        fields = (
            "additional_data",
            "editor",
            "title",
        )

    def create(self, validated_data):
        handle_additional_data(validated_data, self.context["request"].user)
        video = super().create(validated_data)
        update_video_status(video)
        return video

    def update(self, instance, validated_data):
        handle_additional_data(validated_data, self.context["request"].user, instance)
        video = super().update(instance, validated_data)
        update_video_status(video)
        return video


class VideoAdminSearchSerializer(Serializer):
    avg_rating = FloatField(default=0.0, read_only=True)
    edited_at = DateField(allow_null=True, read_only=True)
    editor = UserNestedListSerializer(read_only=True)
    id = IntegerField(read_only=True)
    last_aired = DateField(read_only=True)
    length = IntegerField(read_only=True)
    request_id = IntegerField(read_only=True)
    request_start_datetime = DateTimeField(
        read_only=True, source="request.start_datetime"
    )
    status = IntegerField(read_only=True)
    status_by_admin = SerializerMethodField(read_only=True)
    title = CharField(read_only=True)

    @staticmethod
    def get_status_by_admin(obj) -> bool:
        return is_status_by_admin(obj)
