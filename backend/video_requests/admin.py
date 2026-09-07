from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin

from video_requests.models import Comment, CrewMember, Rating, Request, Todo, Video


def user_change_url(user_id):
    # Built from the model so that swapping AUTH_USER_MODEL cannot break the link.
    options = get_user_model()._meta
    return reverse(
        f"admin:{options.app_label}_{options.model_name}_change", args=(user_id,)
    )


@admin.register(Request)
class RequestHistoryAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "title",
        "status",
        "start_datetime",
        "end_datetime",
        "num_of_videos",
        "requester_link",
    ]
    exclude = ["requested_by"]
    readonly_fields = ["requested_by"]
    search_fields = ["title"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_of_videos=Count("videos"))

    @admin.display(description="Number of Videos")
    def num_of_videos(self, obj):
        return obj.num_of_videos

    @admin.display(description="Requester")
    def requester_link(self, obj):
        url = user_change_url(obj.requester.id)
        return format_html('<a href="{}">{}</a>', url, obj.requester.get_full_name())

    def save_model(self, request, obj, form, change):
        if not change:
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CrewMember)
class CrewMemberHistoryAdmin(SimpleHistoryAdmin):
    list_display = ["id", "request_link", "position", "member_link"]
    search_fields = ["request__title"]

    @admin.display(description="Request")
    def request_link(self, obj):
        url = reverse("admin:video_requests_request_change", args=(obj.request.id,))
        return format_html('<a href="{}">{}</a>', url, obj.request.title)

    @admin.display(description="Crew Member")
    def member_link(self, obj):
        url = user_change_url(obj.member.id)
        return format_html('<a href="{}">{}</a>', url, obj.member.get_full_name())


@admin.register(Video)
class VideoHistoryAdmin(SimpleHistoryAdmin):
    list_display = ["id", "title", "status", "request_link", "avg_rating"]
    search_fields = ["title"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(avg_rating=Avg("ratings__rating"))

    @admin.display(description="Request")
    def request_link(self, obj):
        url = reverse("admin:video_requests_request_change", args=(obj.request.id,))
        return format_html('<a href="{}">{}</a>', url, obj.request.title)

    @admin.display(description="Average Rating")
    def avg_rating(self, obj):
        return obj.avg_rating


@admin.register(Comment)
class CommentHistoryAdmin(SimpleHistoryAdmin):
    list_display = ["id", "request_link", "part_of_comment", "author_link"]
    search_fields = ["request__title"]

    @admin.display(description="Comment")
    def part_of_comment(self, obj):
        return obj.text[:100]

    @admin.display(description="Request")
    def request_link(self, obj):
        url = reverse("admin:video_requests_request_change", args=(obj.request.id,))
        return format_html('<a href="{}">{}</a>', url, obj.request.title)

    @admin.display(description="Author")
    def author_link(self, obj):
        url = user_change_url(obj.author.id)
        return format_html('<a href="{}">{}</a>', url, obj.author.get_full_name())


@admin.register(Rating)
class RatingHistoryAdmin(SimpleHistoryAdmin):
    list_display = [
        "id",
        "video_link",
        "rating",
        "part_of_review",
        "author_link",
    ]
    search_fields = ["request__title"]

    @admin.display(description="Review")
    def part_of_review(self, obj):
        return obj.review[:100]

    @admin.display(description="Video")
    def video_link(self, obj):
        url = reverse("admin:video_requests_video_change", args=(obj.video.id,))
        return format_html('<a href="{}">{}</a>', url, obj.video.title)

    @admin.display(description="Author")
    def author_link(self, obj):
        url = user_change_url(obj.author.id)
        return format_html('<a href="{}">{}</a>', url, obj.author.get_full_name())


@admin.register(Todo)
class TodoAdmin(ModelAdmin):
    list_display = [
        "id",
        "created",
        "request_link",
        "video_link",
        "description",
        "assignee_names",
    ]
    search_fields = ["request__title", "video__title"]

    @admin.display(description="Request")
    def request_link(self, obj):
        url = reverse("admin:video_requests_request_change", args=(obj.request.id,))
        return format_html('<a href="{}">{}</a>', url, obj.request.title)

    @admin.display(description="Video")
    def video_link(self, obj):
        if obj.video:
            url = reverse("admin:video_requests_video_change", args=(obj.video.id,))
            return format_html('<a href="{}">{}</a>', url, obj.video.title)
        return None

    @admin.display(description="Assignees")
    def assignee_names(self, obj):
        return format_html_join(
            mark_safe("&comma;&nbsp;"),  # nosec B308
            '<a href="{}">{}</a>',
            (
                (
                    user_change_url(assignee.id),
                    assignee.get_full_name_eastern_order(),
                )
                for assignee in obj.assignees.all()
            ),
        )
