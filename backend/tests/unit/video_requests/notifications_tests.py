"""Recipients and contents of each task in video_requests/notifications.py.

Which API action queues which task is tested in
tests/workflows/notifications_tests.py.
"""

from unittest.mock import patch

import pytest
import responses
from django.utils import timezone
from model_bakery import baker

from tests.factories import make_user
from tests.helpers.push import subscribe
from video_requests.models import Notification
from video_requests.notifications import (
    notify_crew_new_comment,
    notify_staff_new_request,
    notify_staff_todo_assigned,
    notify_user_new_comment,
    notify_user_request_accepted,
    notify_user_video_published,
    preview,
)

pytestmark = pytest.mark.django_db


def notified(kind):
    return {row.recipient for row in Notification.objects.filter(kind=kind)}


@pytest.fixture
def crewed_request(requester):
    video_request = baker.make(
        "video_requests.Request",
        title="Gólyabál",
        requester=requester,
        responsible=make_user(is_staff=True),
    )
    baker.make(
        "video_requests.CrewMember",
        request=video_request,
        member=make_user(is_staff=True),
        _quantity=2,
    )
    baker.make("video_requests.CrewMember", request=video_request, member=make_user())
    return video_request


def staff_crew(video_request):
    return {row.member for row in video_request.crew.filter(member__is_staff=True)}


def test_a_preview_is_cut_at_120_characters():
    assert preview("a" * 120) == "a" * 120
    assert len(preview("a" * 200)) == 120


class TestComments:
    def test_a_studio_message_reaches_the_requester(
        self, crewed_request, requester, staff_user
    ):
        comment = baker.make(
            "video_requests.Comment",
            request=crewed_request,
            author=staff_user,
            text="x" * 200,
        )

        notify_user_new_comment(comment.id)

        row = Notification.objects.get()
        assert (row.recipient, row.kind, row.request) == (
            requester,
            Notification.Kinds.STUDIO_MESSAGE,
            crewed_request,
        )
        assert row.body == f"Gólyabál: {preview(comment.text)}"

    def test_an_internal_comment_never_reaches_the_requester(
        self, crewed_request, staff_user
    ):
        comment = baker.make(
            "video_requests.Comment",
            request=crewed_request,
            author=staff_user,
            internal=True,
        )

        notify_user_new_comment(comment.id)

        assert not Notification.objects.exists()

    def test_a_banned_requester_gets_no_studio_message(self, staff_user):
        video_request = baker.make(
            "video_requests.Request", requester=make_user(banned=True)
        )
        comment = baker.make(
            "video_requests.Comment", request=video_request, author=staff_user
        )

        notify_user_new_comment(comment.id)

        assert not Notification.objects.exists()

    def test_a_requester_message_reaches_the_crew(
        self, crewed_request, editor_in_chief, requester
    ):
        comment = baker.make(
            "video_requests.Comment", request=crewed_request, author=requester
        )

        notify_crew_new_comment(comment.id)

        assert notified(Notification.Kinds.REQUESTER_MESSAGE) == staff_crew(
            crewed_request
        ) | {editor_in_chief, crewed_request.responsible}

    def test_a_staff_requester_on_the_crew_is_not_told_of_their_own_message(
        self, editor_in_chief
    ):
        staff_requester = make_user(is_staff=True)
        video_request = baker.make("video_requests.Request", requester=staff_requester)
        baker.make(
            "video_requests.CrewMember", request=video_request, member=staff_requester
        )
        comment = baker.make(
            "video_requests.Comment", request=video_request, author=staff_requester
        )

        notify_crew_new_comment(comment.id)

        assert notified(Notification.Kinds.REQUESTER_MESSAGE) == {editor_in_chief}

    def test_an_internal_comment_reaches_the_crew_but_not_its_author(
        self, crewed_request, editor_in_chief
    ):
        comment = baker.make(
            "video_requests.Comment",
            request=crewed_request,
            author=crewed_request.responsible,
            internal=True,
        )

        notify_crew_new_comment(comment.id)

        assert notified(Notification.Kinds.INTERNAL_COMMENT) == staff_crew(
            crewed_request
        ) | {editor_in_chief}

    def test_a_staff_message_to_the_requester_notifies_no_crew(
        self, crewed_request, staff_user
    ):
        comment = baker.make(
            "video_requests.Comment", request=crewed_request, author=staff_user
        )

        notify_crew_new_comment(comment.id)

        assert not Notification.objects.exists()


@pytest.mark.parametrize("banned", [False, True])
def test_an_acceptance_reaches_the_requester_unless_banned(banned):
    video_request = baker.make(
        "video_requests.Request", title="Gólyabál", requester=make_user(banned=banned)
    )

    notify_user_request_accepted(video_request.id)

    rows = Notification.objects.filter(kind=Notification.Kinds.REQUEST_ACCEPTED)
    assert [(row.recipient, row.body) for row in rows] == (
        [] if banned else [(video_request.requester, "Gólyabál")]
    )


@pytest.mark.parametrize("is_staff", [False, True])
def test_a_published_video_reaches_only_an_outside_requester(is_staff):
    video = baker.make(
        "video_requests.Video",
        title="Döntő",
        request=baker.make(
            "video_requests.Request", requester=make_user(is_staff=is_staff)
        ),
    )

    notify_user_video_published(video.id)

    rows = Notification.objects.filter(kind=Notification.Kinds.VIDEO_PUBLISHED)
    assert [(row.recipient, row.request, row.body) for row in rows] == (
        [] if is_staff else [(video.request.requester, video.request, "Döntő")]
    )


def test_a_published_video_skips_a_banned_requester():
    video = baker.make(
        "video_requests.Video",
        request=baker.make("video_requests.Request", requester=make_user(banned=True)),
    )

    notify_user_video_published(video.id)

    assert not Notification.objects.exists()


def test_a_new_request_reaches_the_editors_in_chief_but_not_its_creator(
    editor_in_chief,
):
    creator = make_user(is_staff=True, groups=("Főszerkesztő",))
    video_request = baker.make(
        "video_requests.Request",
        title="Gólyabál",
        requester=make_user(first_name="Anna", last_name="Kiss"),
    )

    notify_staff_new_request(video_request.id, creator.id)

    row = Notification.objects.get()
    assert (row.recipient, row.kind, row.body) == (
        editor_in_chief,
        Notification.Kinds.NEW_REQUEST,
        "Gólyabál · Kiss Anna",
    )


class TestTodoAssigned:
    def test_new_staff_assignees_are_told_but_not_a_creator_assigning_themselves(
        self,
    ):
        creator, assignee = make_user(is_staff=True), make_user(is_staff=True)
        todo = baker.make(
            "video_requests.Todo",
            creator=creator,
            description="Streamkulcs beállítása",
            request=baker.make("video_requests.Request", title="Gólyabál"),
        )

        notify_staff_todo_assigned(todo.id, [creator.id, assignee.id, make_user().id])

        row = Notification.objects.get()
        assert (row.recipient, row.kind, row.body) == (
            assignee,
            Notification.Kinds.TODO_ASSIGNED,
            "Gólyabál: Streamkulcs beállítása",
        )

    def test_a_todo_on_a_video_names_the_video(self):
        video = baker.make("video_requests.Video", title="Döntő")
        todo = baker.make(
            "video_requests.Todo",
            request=video.request,
            video=video,
            description="Vágás",
        )
        assignee = make_user(is_staff=True)

        notify_staff_todo_assigned(todo.id, [assignee.id])

        row = Notification.objects.get()
        assert (row.request, row.body) == (video.request, "Döntő: Vágás")


class TestPush:
    def test_an_acceptance_is_pushed_with_the_unread_count(self, requester):
        baker.make(Notification, recipient=requester)
        baker.make(Notification, recipient=requester, read_at=timezone.now())
        video_request = baker.make(
            "video_requests.Request", title="Gólyabál", requester=requester
        )

        with patch("video_requests.notifications.send_push") as send_push:
            notify_user_request_accepted(video_request.id)

        send_push.assert_called_once_with(
            requester,
            {
                "title": "Elvállaltuk a felkérésed",
                "body": "Gólyabál",
                "url": f"/my-requests/{video_request.id}",
                "tag": f"request:{video_request.id}",
                "unreadCount": 2,
            },
        )

    def test_a_requester_message_is_pushed_to_each_of_the_crew(
        self, crewed_request, editor_in_chief, requester
    ):
        comment = baker.make(
            "video_requests.Comment", request=crewed_request, author=requester
        )

        with patch("video_requests.notifications.send_push") as send_push:
            notify_crew_new_comment(comment.id)

        pushed = [call.args[0] for call in send_push.call_args_list]
        assert len(pushed) == 3
        assert set(pushed) == staff_crew(crewed_request) | {
            editor_in_chief,
            crewed_request.responsible,
        }

    @responses.activate
    def test_a_failing_push_service_still_leaves_the_rows(self, push_on, requester):
        subscription = subscribe(requester)
        responses.post(subscription.endpoint, status=500)
        video_request = baker.make("video_requests.Request", requester=requester)

        notify_user_request_accepted(video_request.id)

        assert len(responses.calls) == 1
        assert Notification.objects.filter(recipient=requester).exists()
