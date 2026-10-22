from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from simple_history.manager import SIMPLE_HISTORY_REVERSE_ATTR_NAME

from video_requests.models import (
    Comment,
    CrewMember,
    DeletedRequest,
    Project,
    Rating,
    Request,
    Todo,
    Video,
)
from video_requests.services import delete_project


def change_link(obj, text):
    options = obj._meta
    url = reverse(
        f"admin:{options.app_label}_{options.model_name}_change", args=(obj.pk,)
    )
    return format_html('<a href="{}">{}</a>', url, text)


def user_link(user):
    return change_link(user, user.get_full_name_eastern_order())


class AddedByMixin:
    added_by_field = None

    def get_readonly_fields(self, request, obj=None):
        return [*super().get_readonly_fields(request, obj), self.added_by_field]

    def save_model(self, request, obj, form, change):
        if not change:
            setattr(obj, self.added_by_field, request.user)
        super().save_model(request, obj, form, change)


class KeepParentMixin:
    parent_fields = []

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj is None:
            return readonly_fields
        return [*readonly_fields, *self.parent_fields]


@admin.register(Project)
class ProjectHistoryAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["responsible"]
    list_display = ["id", "name", "responsible", "created"]
    list_select_related = ["responsible"]
    ordering = ["-id"]
    search_fields = ["name"]

    def delete_model(self, request, obj):
        delete_project(obj)

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for project in queryset:
                delete_project(project)

    def view_on_site(self, obj):
        return obj.admin_url


@admin.register(Request)
class RequestHistoryAdmin(AddedByMixin, SimpleHistoryAdmin):
    added_by_field = "requested_by"
    autocomplete_fields = ["project", "requester", "responsible"]
    list_display = [
        "id",
        "title",
        "status",
        "start_datetime",
        "end_datetime",
        "num_of_videos",
        "requester_link",
    ]
    list_filter = ["status", "project"]
    list_select_related = ["requester"]
    ordering = ["-id"]
    search_fields = ["title"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_of_videos=Count("videos"))

    @admin.display(description=_("Number of videos"), ordering="num_of_videos")
    def num_of_videos(self, obj):
        return obj.num_of_videos

    @admin.display(description=_("Requester"))
    def requester_link(self, obj):
        return user_link(obj.requester)

    def view_on_site(self, obj):
        return obj.admin_url


# A restore brings back only what went with the request: Django deletes the
# rows of a request moments before the request itself.
DELETED_TOGETHER = timedelta(minutes=1)


def restore_deleted_request(deleted):
    def records(model, **filters):
        return model.history.filter(
            history_type="-",
            history_date__range=(
                deleted.history_date - DELETED_TOGETHER,
                deleted.history_date,
            ),
            **filters,
        )

    request = deleted.instance
    # The project may have been deleted since, and full_clean() rejects a
    # missing foreign key.
    if (
        request.project_id
        and not Project.objects.filter(pk=request.project_id).exists()
    ):
        request.project = None

    with transaction.atomic():
        request.save(force_insert=True)
        videos = list(records(Video, request_id=deleted.id))
        for record in [
            *videos,
            *records(Rating, video_id__in=[video.id for video in videos]),
            *records(CrewMember, request_id=deleted.id),
            *records(Comment, request_id=deleted.id),
            *records(Todo, request_id=deleted.id),
        ]:
            obj = record.instance
            obj.save(force_insert=True)
            if isinstance(obj, Todo):
                obj.assignees.set(record.assignees.values_list("user", flat=True))


@admin.register(DeletedRequest)
class DeletedRequestAdmin(admin.ModelAdmin):
    actions = ["restore"]
    list_display = ["id", "title", "start_datetime", "deleted", "deleted_by"]
    list_display_links = None
    list_select_related = ["history_user"]
    ordering = ["-history_date"]
    search_fields = ["title"]

    def get_queryset(self, request):
        # A request is still deleted when its latest version is a deletion.
        latest = Request.history.filter(id=OuterRef("id")).order_by(
            "-history_date", "-history_id"
        )
        return (
            super()
            .get_queryset(request)
            .filter(
                history_type="-",
                history_date__gte=now() - timedelta(days=settings.TRIMMED_HISTORY_DAYS),
                history_id=Subquery(latest.values("history_id")[:1]),
            )
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Deleted at"), ordering="history_date")
    def deleted(self, obj):
        return obj.history_date

    @admin.display(description=_("Deleted by"))
    def deleted_by(self, obj):
        return obj.history_user and user_link(obj.history_user)

    @admin.action(
        description=_("Restore selected requests with everything deleted with them")
    )
    def restore(self, request, queryset):
        for deleted in queryset:
            restore_deleted_request(deleted)
            self.message_user(
                request, _("Restored: %(title)s") % {"title": deleted.title}
            )


@admin.register(CrewMember)
class CrewMemberHistoryAdmin(KeepParentMixin, SimpleHistoryAdmin):
    autocomplete_fields = ["request", "member"]
    list_display = ["id", "request_link", "position", "member_link"]
    list_select_related = ["request", "member"]
    parent_fields = ["request"]
    search_fields = ["request__title"]

    @admin.display(description=_("Request"))
    def request_link(self, obj):
        return change_link(obj.request, obj.request.title)

    @admin.display(description=_("Crew member"))
    def member_link(self, obj):
        return user_link(obj.member)


@admin.register(Video)
class VideoHistoryAdmin(KeepParentMixin, SimpleHistoryAdmin):
    autocomplete_fields = ["request", "editor"]
    list_display = ["id", "title", "status", "request_link", "avg_rating"]
    list_filter = ["status"]
    ordering = ["-id"]
    parent_fields = ["request"]
    search_fields = ["title"]

    def get_queryset(self, request):
        # Here rather than list_select_related: the video autocompletes run this
        # queryset too, and label each video with the title of its request.
        return super().get_queryset(request).select_related("request")

    @admin.display(description=_("Request"))
    def request_link(self, obj):
        return change_link(obj.request, obj.request.title)

    @admin.display(description=_("Average rating"), ordering="avg_rating")
    def avg_rating(self, obj):
        return obj.avg_rating  # Annotated by Video.objects.

    def view_on_site(self, obj):
        return obj.admin_url


@admin.register(Comment)
class CommentHistoryAdmin(AddedByMixin, KeepParentMixin, SimpleHistoryAdmin):
    added_by_field = "author"
    autocomplete_fields = ["request"]
    list_display = ["id", "request_link", "part_of_comment", "internal", "author_link"]
    list_filter = ["internal"]
    list_select_related = ["request", "author"]
    parent_fields = ["request"]
    search_fields = ["request__title"]

    @admin.display(description=_("Comment"))
    def part_of_comment(self, obj):
        return obj.text[:100]

    @admin.display(description=_("Request"))
    def request_link(self, obj):
        return change_link(obj.request, obj.request.title)

    @admin.display(description=_("Author"))
    def author_link(self, obj):
        return user_link(obj.author)


@admin.register(Rating)
class RatingHistoryAdmin(AddedByMixin, KeepParentMixin, SimpleHistoryAdmin):
    added_by_field = "author"
    autocomplete_fields = ["video"]
    list_display = [
        "id",
        "video_link",
        "rating",
        "part_of_review",
        "author_link",
    ]
    list_select_related = ["video", "author"]
    parent_fields = ["video"]
    search_fields = ["video__title", "video__request__title"]

    @admin.display(description=_("Review"))
    def part_of_review(self, obj):
        return obj.review[:100]

    @admin.display(description=_("Video"))
    def video_link(self, obj):
        return change_link(obj.video, obj.video.title)

    @admin.display(description=_("Author"))
    def author_link(self, obj):
        return user_link(obj.author)


class TodoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A version opened from the history must show the assignees it had,
        # while Django reads them from the current rows of the todo.
        record = getattr(self.instance, SIMPLE_HISTORY_REVERSE_ATTR_NAME, None)
        if record is not None:
            self.initial["assignees"] = list(
                record.assignees.values_list("user", flat=True)
            )


@admin.register(Todo)
class TodoHistoryAdmin(AddedByMixin, KeepParentMixin, SimpleHistoryAdmin):
    added_by_field = "creator"
    autocomplete_fields = ["request", "video", "assignees"]
    form = TodoForm
    list_display = [
        "id",
        "created",
        "request_link",
        "video_link",
        "description",
        "status",
        "assignee_names",
    ]
    list_filter = ["status"]
    list_select_related = ["request", "video"]
    parent_fields = ["request", "video"]
    search_fields = ["request__title", "video__title"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("assignees")

    @admin.display(description=_("Request"))
    def request_link(self, obj):
        return change_link(obj.request, obj.request.title)

    @admin.display(description=_("Video"))
    def video_link(self, obj):
        if obj.video:
            return change_link(obj.video, obj.video.title)
        return None

    @admin.display(description=_("Assignees"))
    def assignee_names(self, obj):
        return format_html_join(
            ", ", "{}", ((user_link(assignee),) for assignee in obj.assignees.all())
        )
