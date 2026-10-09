from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from video_requests.models import Comment, CrewMember, Rating, Request, Todo, Video


def change_link(obj, text):
    options = obj._meta
    url = reverse(
        f"admin:{options.app_label}_{options.model_name}_change", args=(obj.pk,)
    )
    return format_html('<a href="{}">{}</a>', url, text)


def user_link(user):
    return change_link(user, user.get_full_name_eastern_order())


@admin.register(Request)
class RequestHistoryAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["requester", "responsible"]
    list_display = [
        "id",
        "title",
        "status",
        "start_datetime",
        "end_datetime",
        "num_of_videos",
        "requester_link",
    ]
    list_filter = ["status"]
    list_select_related = ["requester"]
    ordering = ["-id"]
    readonly_fields = ["requested_by"]
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

    def save_model(self, request, obj, form, change):
        if not change:
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrewMember)
class CrewMemberHistoryAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["request", "member"]
    list_display = ["id", "request_link", "position", "member_link"]
    list_select_related = ["request", "member"]
    search_fields = ["request__title"]

    @admin.display(description=_("Request"))
    def request_link(self, obj):
        return change_link(obj.request, obj.request.title)

    @admin.display(description=_("Crew member"))
    def member_link(self, obj):
        return user_link(obj.member)


@admin.register(Video)
class VideoHistoryAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["request", "editor"]
    list_display = ["id", "title", "status", "request_link", "avg_rating"]
    list_filter = ["status"]
    ordering = ["-id"]
    search_fields = ["title"]

    def get_queryset(self, request):
        # Here rather than list_select_related: the video autocompletes run this
        # queryset too, and label each video with the title of its request.
        return super().get_queryset(request).select_related("request")

    def get_readonly_fields(self, request, obj=None):
        return [] if obj is None else ["request"]

    @admin.display(description=_("Request"))
    def request_link(self, obj):
        return change_link(obj.request, obj.request.title)

    @admin.display(description=_("Average rating"), ordering="avg_rating")
    def avg_rating(self, obj):
        return obj.avg_rating  # Annotated by Video.objects.

    def view_on_site(self, obj):
        return obj.admin_url


@admin.register(Comment)
class CommentHistoryAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["request", "author"]
    list_display = ["id", "request_link", "part_of_comment", "internal", "author_link"]
    list_filter = ["internal"]
    list_select_related = ["request", "author"]
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
class RatingHistoryAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["video", "author"]
    list_display = [
        "id",
        "video_link",
        "rating",
        "part_of_review",
        "author_link",
    ]
    list_select_related = ["video", "author"]
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


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    autocomplete_fields = ["request", "video", "creator", "assignees"]
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
