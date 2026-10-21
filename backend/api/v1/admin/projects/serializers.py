from rest_framework.fields import (
    CharField,
    DateTimeField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.serializers import Serializer

from api.v1.admin.requests.helpers import is_status_by_admin
from api.v1.admin.users.serializers import (
    UserNestedDetailSerializer,
    UserNestedListSerializer,
)


class ProjectAdminListSerializer(Serializer):
    first_start = DateTimeField(read_only=True, allow_null=True)
    id = IntegerField(read_only=True)
    last_end = DateTimeField(read_only=True, allow_null=True)
    name = CharField(read_only=True)
    request_count = IntegerField(read_only=True)
    responsible = UserNestedListSerializer(read_only=True, allow_null=True)


class ProjectRequestSerializer(Serializer):
    end_datetime = DateTimeField(read_only=True)
    id = IntegerField(read_only=True)
    place = CharField(read_only=True)
    start_datetime = DateTimeField(read_only=True)
    status = IntegerField(read_only=True)
    status_by_admin = SerializerMethodField(read_only=True)
    title = CharField(read_only=True)
    type = CharField(read_only=True)

    @staticmethod
    def get_status_by_admin(obj) -> bool:
        return is_status_by_admin(obj)


class ProjectAdminRetrieveSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    requests = ProjectRequestSerializer(many=True, read_only=True)
    responsible = UserNestedDetailSerializer(read_only=True, allow_null=True)
