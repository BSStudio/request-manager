from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateField, IntegerField
from rest_framework.serializers import Serializer


class ReportAdminQuerySerializer(Serializer):
    date_after = DateField()
    date_before = DateField()

    def validate(self, data):
        if data["date_before"] < data["date_after"]:
            raise ValidationError(
                {"date_after": [_("The start of the period cannot be after its end.")]}
            )
        return data


class ReportAdminSerializer(Serializer):
    class ReportItemSerializer(Serializer):
        date = DateField(read_only=True)
        id = IntegerField(read_only=True)
        title = CharField(read_only=True)

    requests = ReportItemSerializer(many=True, read_only=True)
    videos = ReportItemSerializer(many=True, read_only=True)
