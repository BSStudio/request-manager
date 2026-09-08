from common.models import User
from video_requests.models import Comment, Request


def create_comment(*, author: User, text: str, request: Request) -> Comment:
    return Comment.objects.create(author=author, text=text, request=request)
