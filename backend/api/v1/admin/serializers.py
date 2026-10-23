import json

from rest_framework.fields import CharField, DateTimeField, IntegerField
from rest_framework.serializers import Serializer

from api.v1.admin.users.serializers import UserNestedListSerializer


class HistoryValueField(CharField):
    def to_representation(self, value):
        # str() of a JSON field's value is Python syntax, not JSON.
        if isinstance(value, dict | list):
            return json.dumps(value)
        return super().to_representation(value)


class HistoryChangesSerializer(Serializer):
    field = CharField(read_only=True)
    new = HistoryValueField(read_only=True)
    old = HistoryValueField(read_only=True)


class HistorySerializer(Serializer):
    changes = HistoryChangesSerializer(many=True, read_only=True)
    date = DateTimeField(read_only=True, source="new_record.history_date")
    user = UserNestedListSerializer(read_only=True, source="new_record.history_user")


class ProjectNestedSerializer(Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
