from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField,
    DateTimeField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, Serializer

from api.v1.admin.requests.helpers import is_status_by_admin
from api.v1.admin.requests.requests.serializers import RequestAdminCreateSerializer
from api.v1.admin.users.serializers import (
    UserNestedDetailSerializer,
    UserNestedListSerializer,
)
from video_requests.models import Project, Request
from video_requests.services import set_project


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


class ProjectAdminWriteSerializer(ModelSerializer):
    add_requests = PrimaryKeyRelatedField(
        many=True, queryset=Request.objects.all(), required=False, write_only=True
    )
    new_requests = RequestAdminCreateSerializer(
        many=True, required=False, write_only=True
    )
    remove_requests = PrimaryKeyRelatedField(
        many=True, queryset=Request.objects.all(), required=False, write_only=True
    )

    class Meta:
        model = Project
        fields = (
            "add_requests",
            "name",
            "new_requests",
            "remove_requests",
            "responsible",
        )

    def __init__(self, *args, **kwargs):
        # A partial serializer skips missing required fields in nested rows too,
        # and a new request needs them all. Only the name may be left out of an
        # update.
        kwargs["partial"] = False
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["name"].required = False

    def validate_add_requests(self, requests):
        project_id = self.instance.pk if self.instance else None
        for request in requests:
            if request.project_id not in (None, project_id):
                raise ValidationError(
                    _("%(title)s belongs to another project.")
                    % {"title": request.title}
                )
        return requests

    def validate_remove_requests(self, requests):
        for request in requests:
            if self.instance is None or request.project_id != self.instance.pk:
                raise ValidationError(
                    _("%(title)s is not in this project.") % {"title": request.title}
                )
        return requests

    def create(self, validated_data):
        changes = self._pop_changes(validated_data)
        with transaction.atomic():
            project = super().create(validated_data)
            self._apply_changes(project, **changes)
        return project

    def update(self, instance, validated_data):
        changes = self._pop_changes(validated_data)
        with transaction.atomic():
            project = super().update(instance, validated_data)
            self._apply_changes(project, **changes)
        return project

    @staticmethod
    def _pop_changes(validated_data):
        return {
            field: validated_data.pop(field, [])
            for field in ("add_requests", "new_requests", "remove_requests")
        }

    def _apply_changes(self, project, add_requests, new_requests, remove_requests):
        self._set_project(add_requests, project, "add_requests")
        self._set_project(remove_requests, None, "remove_requests")
        self._create_requests(new_requests, project)

    @staticmethod
    def _set_project(requests, project, field):
        for request in requests:
            try:
                set_project(request, project)
            except DjangoValidationError as error:
                raise ValidationError(
                    {
                        field: [
                            f"{request.title}: {message}" for message in error.messages
                        ]
                    }
                )

    def _create_requests(self, rows, project):
        user = self.context["request"].user
        errors = [{} for row in rows]
        for index, row in enumerate(rows):
            row.pop("send_notification", None)
            # Request.clean() runs in save(), after the validation that would
            # have put its errors under the row's index. It raises before the
            # INSERT, so the other rows can still be tried; the atomic() around
            # the save undoes the ones that went in.
            try:
                RequestAdminCreateSerializer(context=self.context).create(
                    {**row, "project": project, "requested_by": user}
                )
            except DjangoValidationError as error:
                errors[index] = (
                    error.message_dict
                    if hasattr(error, "error_dict")
                    else {"non_field_errors": error.messages}
                )
        if any(errors):
            raise ValidationError({"new_requests": errors})
