from collections.abc import Iterable

from celery import shared_task
from django.utils.text import Truncator

from common.models import User
from common.push import push_enabled, send_push
from common.utilities import get_editor_in_chief
from video_requests.models import Comment, Notification, Request, Todo, Video

PREVIEW_LENGTH = 120
RETENTION_DAYS = 30


def preview(text: str) -> str:
    return Truncator(text).chars(PREVIEW_LENGTH)


def get_crew_users(request: Request) -> set[User]:
    """The people the crew e-mails go to: the staff crew, the editor in chief and a staff responsible."""
    users = {
        crew_member.member
        for crew_member in request.crew.select_related("member").filter(
            member__is_staff=True
        )
    }
    users.update(get_editor_in_chief())
    if request.responsible and request.responsible.is_staff:
        users.add(request.responsible)
    return users


def push_payload(notification: Notification) -> dict:
    return {
        "title": str(notification.title),
        "body": notification.body,
        "url": notification.url,
        "tag": f"request:{notification.request_id}",
        "unreadCount": notification.recipient.notifications.filter(
            read_at__isnull=True
        ).count(),
    }


def notify(
    recipients: Iterable[User],
    *,
    kind: str,
    request: Request,
    body: str,
    actor: User | None = None,
) -> list[Notification]:
    rows = Notification.objects.bulk_create(
        Notification(recipient=recipient, kind=kind, request=request, body=body)
        for recipient in set(recipients)
        if recipient != actor
    )
    if push_enabled():
        for notification in rows:
            send_push(notification.recipient, push_payload(notification))
    return rows


def comment_body(comment: Comment) -> str:
    return f"{comment.request.title}: {preview(comment.text)}"


@shared_task
def notify_user_new_comment(comment_id):
    comment = Comment.objects.select_related("author", "request__requester").get(
        pk=comment_id
    )
    requester = comment.request.requester
    rows = notify(
        [] if comment.internal or requester.is_banned else [requester],
        kind=Notification.Kinds.STUDIO_MESSAGE,
        request=comment.request,
        body=comment_body(comment),
        actor=comment.author,
    )
    return f"{len(rows)} new comment notifications were created."


@shared_task
def notify_crew_new_comment(comment_id):
    comment = Comment.objects.select_related("author", "request__responsible").get(
        pk=comment_id
    )
    if comment.internal:
        kind = Notification.Kinds.INTERNAL_COMMENT
    elif comment.author_id == comment.request.requester_id:
        kind = Notification.Kinds.REQUESTER_MESSAGE
    else:
        return "A message to the requester notifies no crew."
    rows = notify(
        get_crew_users(comment.request),
        kind=kind,
        request=comment.request,
        body=comment_body(comment),
        actor=comment.author,
    )
    return f"{len(rows)} new comment notifications were created."


@shared_task
def notify_user_request_accepted(request_id):
    request = Request.objects.select_related("requester").get(pk=request_id)
    rows = notify(
        [] if request.requester.is_banned else [request.requester],
        kind=Notification.Kinds.REQUEST_ACCEPTED,
        request=request,
        body=request.title,
    )
    return f"{len(rows)} request accepted notifications were created."


@shared_task
def notify_user_video_published(video_id):
    video = Video.objects.select_related("request__requester").get(pk=video_id)
    requester = video.request.requester
    rows = notify(
        [] if requester.is_banned or requester.is_staff else [requester],
        kind=Notification.Kinds.VIDEO_PUBLISHED,
        request=video.request,
        body=video.title,
    )
    return f"{len(rows)} video published notifications were created."


@shared_task
def notify_staff_new_request(request_id, actor_id):
    request = Request.objects.select_related("requester").get(pk=request_id)
    rows = notify(
        get_editor_in_chief(),
        kind=Notification.Kinds.NEW_REQUEST,
        request=request,
        body=f"{request.title} · {request.requester.get_full_name_eastern_order()}",
        actor=User.objects.filter(pk=actor_id).first(),
    )
    return f"{len(rows)} new request notifications were created."


@shared_task
def notify_staff_todo_assigned(todo_id, user_ids):
    todo = Todo.objects.select_related("creator", "request", "video").get(pk=todo_id)
    title = todo.video.title if todo.video else todo.request.title
    rows = notify(
        User.objects.filter(id__in=user_ids, is_staff=True),
        kind=Notification.Kinds.TODO_ASSIGNED,
        request=todo.request,
        body=f"{title}: {preview(todo.description)}",
        actor=todo.creator,
    )
    return f"{len(rows)} todo assigned notifications were created."
