from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Avg, JSONField
from django.utils.translation import gettext_lazy as _
from jsonschema import FormatChecker
from jsonschema import ValidationError as JsonValidationError
from jsonschema import validate
from simple_history.models import HistoricalRecords

from common.models import (
    AbstractComment,
    AbstractRating,
    AbstractTodo,
    get_sentinel_user,
)
from video_requests.schemas import (
    REQUEST_ADDITIONAL_DATA_SCHEMA,
    VIDEO_ADDITIONAL_DATA_SCHEMA,
)


def validate_request_additional_data(value):
    try:
        validate(value, REQUEST_ADDITIONAL_DATA_SCHEMA, format_checker=FormatChecker())
    except JsonValidationError as e:
        raise ValidationError(e)


def validate_video_additional_data(value):
    try:
        validate(value, VIDEO_ADDITIONAL_DATA_SCHEMA, format_checker=FormatChecker())
    except JsonValidationError as e:
        raise ValidationError(e)


class AnnotatedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(avg_rating=Avg("ratings__rating"))


class Request(models.Model):
    class Statuses(models.IntegerChoices):
        DENIED = 0, _("Elutasítva")
        REQUESTED = 1, _("Felkérés")
        ACCEPTED = 2, _("Elvállalva")
        RECORDED = 3, _("Leforgatva")
        UPLOADED = 4, _("Beírva")
        EDITED = 5, _("Megvágva")
        ARCHIVED = 6, _("Archiválva")
        DONE = 7, _("Lezárva")
        CANCELED = 9, _("Szervezők által lemondva")
        FAILED = 10, _("Meghiúsult")

    title = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    deadline = models.DateField(blank=True)
    type = models.CharField(max_length=50)
    place = models.CharField(max_length=150)
    status = models.PositiveSmallIntegerField(
        choices=Statuses, default=Statuses.REQUESTED, db_index=True
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="responsible_requests",
        on_delete=models.SET(get_sentinel_user),
        blank=True,
        null=True,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="requested_requests",
        on_delete=models.SET(get_sentinel_user),
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="submitted_requests",
        on_delete=models.SET(get_sentinel_user),
    )
    additional_data = JSONField(
        encoder=DjangoJSONEncoder,
        validators=[validate_request_additional_data],
        default=dict,
        blank=True,
    )
    history = HistoricalRecords()

    @property
    def url(self) -> str:
        return f"{settings.BASE_URL}/my-requests/{self.id}"

    @property
    def admin_url(self) -> str:
        return f"{settings.BASE_URL}/admin/requests/{self.id}"

    def clean(self):
        if self.start_datetime > self.end_datetime:
            raise ValidationError(
                {"end_datetime": [_("Must be later than the start of the event.")]}
            )
        if self.deadline and self.end_datetime.date() >= self.deadline:
            raise ValidationError(
                {"deadline": [_("Must be later than the end of the event.")]}
            )

    def get_owner(self):
        return self.requester

    def save(self, *args, **kwargs):
        if not self.deadline:
            self.deadline = (self.end_datetime + timedelta(weeks=3)).date()
        self.full_clean(exclude=["additional_data"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} || {self.start_datetime.date()}"


class CrewMember(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="crew")
    position = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.request.title} || {self.member.get_full_name_eastern_order()} - {self.position}"


class Video(models.Model):
    class Statuses(models.IntegerChoices):
        PENDING = 1, _("Vágásra vár")
        IN_PROGRESS = 2, _("Vágás alatt")
        EDITED = 3, _("Megvágva")
        CODED = 4, _("Kikódolva")
        PUBLISHED = 5, _("Közzétéve")
        DONE = 6, _("Lezárva")

    title = models.CharField(max_length=200)
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="videos"
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        blank=True,
        null=True,
    )
    status = models.PositiveSmallIntegerField(
        choices=Statuses, default=Statuses.PENDING, db_index=True
    )
    additional_data = JSONField(
        encoder=DjangoJSONEncoder,
        validators=[validate_video_additional_data],
        default=dict,
        blank=True,
    )
    history = HistoricalRecords()
    objects = AnnotatedManager()

    __original_aired = None

    def get_owner(self):
        return self.request.requester

    @property
    def published_url(self) -> str:
        published_url = self.additional_data.get("publishing", {}).get("website")
        return published_url

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_aired = self.additional_data.get("aired", None)

    def save(self, *args, **kwargs):
        aired = self.additional_data.get("aired", None)
        if aired and aired != self.__original_aired:
            aired.sort(
                key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request.title} || {self.title}"


class Comment(AbstractComment):
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"{self.request.title} || {self.text} - {self.author.get_full_name_eastern_order()}"


class Rating(AbstractRating):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="ratings")

    def __str__(self):
        return f"{self.video.title} || {self.author.get_full_name_eastern_order()} ({self.rating})"


class Todo(AbstractTodo):
    class Statuses(models.IntegerChoices):
        OPEN = 1, _("Nyitva")
        CLOSED = 2, _("Lezárva")
        DISCARDED = 3, _("Elvetve")

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="todos")
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="todos", blank=True, null=True
    )
    status = models.PositiveSmallIntegerField(
        choices=Statuses, default=Statuses.OPEN, db_index=True
    )

    def __str__(self):
        return f"Todo || {self.request.title} - {self.description[0:25]}[...]"
