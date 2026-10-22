from django.db import transaction

from common.models import User
from common.utilities import create_calendar_event
from video_requests.emails import email_user_new_request_confirmation
from video_requests.models import Comment, Project, Request
from video_requests.notifications import notify_staff_new_request
from video_requests.utilities import update_request_status


def create_comment(*, author: User, text: str, request: Request) -> Comment:
    return Comment.objects.create(author=author, text=text, request=request)


def create_request(
    *,
    comment: str | None = None,
    comment_author: User | None = None,
    created_by: User | None = None,
    send_confirmation: bool = True,
    **fields,
) -> Request:
    request = Request.objects.create(**fields)
    if comment:
        create_comment(
            author=comment_author or request.requester, text=comment, request=request
        )
    # Admins can create a request that is already accepted.
    update_request_status(request)
    create_calendar_event.delay_on_commit(request.id)
    if send_confirmation:
        email_user_new_request_confirmation.delay_on_commit(request.id)
    notify_staff_new_request.delay_on_commit(
        request.id, (created_by or request.requester).id
    )
    return request


def set_project(request: Request, project: Project | None) -> None:
    # A save rather than QuerySet.update(): simple-history and cacheops only
    # notice saves.
    request.project = project
    request.save(update_fields=["project"])


def delete_project(project: Project) -> None:
    with transaction.atomic():
        for request in project.requests.all():
            set_project(request, None)
        project.delete()
