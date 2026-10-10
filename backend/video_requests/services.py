from common.models import User
from common.utilities import create_calendar_event
from video_requests.emails import email_user_new_request_confirmation
from video_requests.models import Comment, Request
from video_requests.utilities import update_request_status


def create_comment(*, author: User, text: str, request: Request) -> Comment:
    return Comment.objects.create(author=author, text=text, request=request)


def create_request(
    *,
    comment: str | None = None,
    comment_author: User | None = None,
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
    create_calendar_event.delay(request.id)
    if send_confirmation:
        email_user_new_request_confirmation.delay(request.id)
    return request
