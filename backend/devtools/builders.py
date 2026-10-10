from collections.abc import Iterable
from datetime import date, datetime, time, timedelta

from django.utils import timezone
from django.utils.text import slugify

from common.models import User
from video_requests.models import Comment, CrewMember, Rating, Request, Todo, Video


def at(days: int, hour: int) -> datetime:
    """``hour`` o'clock local time, ``days`` days from today; negative is the past."""
    day = timezone.localdate() + timedelta(days=days)
    return timezone.make_aware(datetime.combine(day, time(hour)))


def create_request(
    title: str,
    *,
    requester: User,
    start: datetime,
    hours: int,
    type: str,
    place: str,
    responsible: User | None = None,
    requested_by: User | None = None,
    additional_data: dict | None = None,
    created: datetime | None = None,
) -> Request:
    """Without ``created``, submitted three weeks before the event, or now."""
    request = Request.objects.create(
        title=title,
        start_datetime=start,
        end_datetime=start + timedelta(hours=hours),
        type=type,
        place=place,
        requester=requester,
        requested_by=requested_by or requester,
        responsible=responsible,
        additional_data=additional_data or {},
    )
    _backdate(request, created or min(timezone.now(), start - timedelta(weeks=3)))
    return request


def _backdate(instance: Request | Comment, created: datetime) -> None:
    # auto_now_add ignores a value passed to create(), and a later save() writes
    # back whatever the instance holds.
    instance.created = created
    type(instance).objects.filter(pk=instance.pk).update(created=created)


def add_video(
    request: Request,
    title: str,
    status: int = Video.Statuses.PENDING,
    *,
    editor: User | None = None,
    aired: tuple[date, ...] = (),
) -> Video:
    # Created at its final status: update_video_status opens a sharing todo and
    # e-mails the requester only for a video that moves up to published.
    return Video.objects.create(
        request=request,
        title=title,
        status=status,
        editor=editor,
        additional_data=_video_data(request, title, status, aired),
    )


def _video_data(request: Request, title: str, status: int, aired) -> dict:
    data = {}
    if status >= Video.Statuses.EDITED:
        data["editing_done"] = True
    if status >= Video.Statuses.CODED:
        data["coding"] = {"website": True}
    if status >= Video.Statuses.PUBLISHED:
        data["publishing"] = {
            "website": f"https://example.com/videok/{slugify(f'{request.title} {title}')}",
            "email_sent_to_user": True,
        }
    if status >= Video.Statuses.DONE:
        data["archiving"] = {"hq_archive": True}
    if aired:
        data["aired"] = [day.isoformat() for day in aired]
    return data


def add_comment(
    request: Request,
    author: User,
    text: str,
    *,
    created: datetime,
    internal: bool = False,
) -> Comment:
    comment = Comment.objects.create(
        request=request, author=author, text=text, internal=internal
    )
    _backdate(comment, created)
    return comment


def add_crew(request: Request, *crew: tuple[User, str]) -> None:
    CrewMember.objects.bulk_create(
        CrewMember(request=request, member=member, position=position)
        for member, position in crew
    )


def add_rating(video: Video, author: User, rating: int, review: str = "") -> Rating:
    return Rating.objects.create(
        video=video, author=author, rating=rating, review=review
    )


def add_todo(
    request: Request,
    creator: User,
    description: str,
    *,
    assignees: Iterable[User] = (),
    status: int = Todo.Statuses.OPEN,
    video: Video | None = None,
) -> Todo:
    todo = Todo.objects.create(
        request=request,
        creator=creator,
        description=description,
        status=status,
        video=video,
    )
    # Through the table, because assignees.add() would e-mail each of them.
    Todo.assignees.through.objects.bulk_create(
        Todo.assignees.through(todo=todo, user=user) for user in assignees
    )
    return todo
