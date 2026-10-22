from rest_framework.fields import BooleanField, CharField, DateTimeField, IntegerField
from rest_framework.serializers import ModelSerializer, Serializer

from api.v1.admin.users.serializers import UserNestedListSerializer
from video_requests.emails import email_crew_new_comment, email_user_new_comment
from video_requests.models import Comment


class CommentAdminListRetrieveSerializer(Serializer):
    author = UserNestedListSerializer(read_only=True)
    created = DateTimeField(read_only=True)
    id = IntegerField(read_only=True)
    internal = BooleanField(read_only=True)
    text = CharField(read_only=True)


class CommentAdminCreateUpdateSerializer(ModelSerializer):
    author = UserNestedListSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["author", "created", "id", "internal", "text"]
        read_only_fields = ["author", "created", "id"]

    def create(self, validated_data):
        comment = super().create(validated_data)
        if not comment.internal and not comment.request.requester.is_banned:
            email_user_new_comment.delay(comment.id)
        email_crew_new_comment.delay(comment.id)
        return comment
