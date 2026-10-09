"""Subject and recipients of each builder in video_requests/emails.py.

When a message is sent is tested in tests/workflows/notifications_tests.py and
tests/management_commands/scheduled_emails_tests.py. Staff-only recipients (the
responsible, the crew, the assignees) drop anyone who is not staff.
"""

import pytest
from django.conf import settings as django_settings
from django.core import mail
from model_bakery import baker

from tests.factories import make_user
from video_requests.emails import (
    email_crew_daily_reminder,
    email_crew_new_comment,
    email_crew_request_modified,
    email_production_manager_unfinished_requests,
    email_responsible_overdue_request,
    email_staff_todo_assigned,
    email_staff_weekly_tasks,
    email_user_new_comment,
    email_user_new_request_confirmation,
    email_user_video_published,
)

pytestmark = [pytest.mark.django_db, pytest.mark.emails]


@pytest.fixture
def video_request(requester):
    return baker.make(
        "video_requests.Request",
        title="Test Request",
        requester=requester,
        responsible=make_user(is_staff=True),
    )


@pytest.fixture
def crew(video_request):
    """Two staff members, and one outsider who must never be written to."""
    return [
        baker.make(
            "video_requests.CrewMember",
            request=video_request,
            member=make_user(is_staff=is_staff),
        )
        for is_staff in (True, True, False)
    ]


def only_message():
    assert len(mail.outbox) == 1
    return mail.outbox[0]


def staff_emails(crew):
    return {member.member.email for member in crew if member.member.is_staff}


class TestToTheRequester:
    def test_new_request_confirmation(self, editor_in_chief, requester, video_request):
        email_user_new_request_confirmation(video_request.id)

        message = only_message()
        assert message.subject == "Test Request | Forgatási felkérésedet fogadtuk"
        assert message.to == [requester.email]
        assert message.cc == [django_settings.DEFAULT_REPLY_EMAIL]
        assert message.bcc == [editor_in_chief.email]
        assert message.reply_to == [django_settings.DEFAULT_REPLY_EMAIL]

    def test_video_published_marks_the_video_as_announced(
        self, requester, video_request
    ):
        video = baker.make(
            "video_requests.Video",
            request=video_request,
            additional_data={"publishing": {"website": "https://example.com"}},
        )

        email_user_video_published(video.id)

        message = only_message()
        assert message.subject == "Test Request | Új videót publikáltunk"
        assert message.to == [requester.email]
        assert message.reply_to == [django_settings.DEFAULT_REPLY_EMAIL]
        video.refresh_from_db()
        assert video.additional_data["publishing"]["email_sent_to_user"] is True

    def test_new_comment(self, requester, staff_user, video_request):
        comment = baker.make(
            "video_requests.Comment", request=video_request, author=staff_user
        )

        email_user_new_comment(comment.id)

        message = only_message()
        assert message.subject == "Test Request | Új üzenet a BSS-től"
        assert message.to == [requester.email]
        assert message.reply_to == [django_settings.DEFAULT_REPLY_EMAIL]


class TestToTheCrew:
    """The staff crew, with the editor-in-chief and a staff responsible copied in."""

    def test_new_comment(self, crew, editor_in_chief, staff_user, video_request):
        comment = baker.make(
            "video_requests.Comment", request=video_request, author=staff_user
        )

        email_crew_new_comment(comment.id)

        message = only_message()
        assert message.subject == "Test Request | Új üzenet a felkérőnek"
        assert set(message.to) == staff_emails(crew)
        assert set(message.cc) == {
            editor_in_chief.email,
            video_request.responsible.email,
        }

    def test_new_comment_from_the_requester(self, crew, requester, video_request):
        comment = baker.make(
            "video_requests.Comment", request=video_request, author=requester
        )

        email_crew_new_comment(comment.id)

        assert only_message().subject == "Test Request | Új üzenet a felkérőtől"

    def test_new_internal_comment(self, crew, staff_user, video_request):
        comment = baker.make(
            "video_requests.Comment",
            request=video_request,
            author=staff_user,
            internal=True,
        )

        email_crew_new_comment(comment.id)

        assert only_message().subject == "Test Request | Új belső megjegyzés"

    def test_request_modified(self, crew, editor_in_chief, video_request):
        email_crew_request_modified(
            video_request.id,
            "Staff Test",
            "2020-11-19 10:20",
            [{"name": "Helyszín", "previous": "Old place", "next": "New place"}],
        )

        message = only_message()
        assert message.subject == "Test Request | Felkérés módosítva"
        assert set(message.to) == staff_emails(crew)
        assert set(message.cc) == {
            editor_in_chief.email,
            video_request.responsible.email,
        }

    def test_a_responsible_who_is_not_staff_is_left_off(
        self, crew, editor_in_chief, video_request
    ):
        video_request.responsible = make_user()
        video_request.save()

        email_crew_request_modified(video_request.id, "Staff Test", "", [])

        assert only_message().cc == [editor_in_chief.email]

    def test_daily_reminder(self, crew, video_request):
        email_crew_daily_reminder(video_request, crew[:2])

        message = only_message()
        assert message.subject == "Emlékeztető | Test Request | Mai forgatás"
        assert set(message.to) == staff_emails(crew)


class TestToStaff:
    @pytest.mark.parametrize("on_a_video", [False, True], ids=["request", "video"])
    def test_todo_assigned_only_reaches_staff(self, on_a_video, video_request):
        staff = make_user(is_staff=True)
        outsider = make_user()
        todo = baker.make(
            "video_requests.Todo",
            request=video_request,
            video=(
                baker.make("video_requests.Video", request=video_request)
                if on_a_video
                else None
            ),
        )

        email_staff_todo_assigned(todo.id, [staff.id, outsider.id])

        message = only_message()
        assert message.subject == "Feladatot rendeltek hozzád"
        assert message.to == [staff.email]

    def test_weekly_tasks(self):
        email_staff_weekly_tasks([], [], [])

        message = only_message()
        assert message.subject == "E heti forgatások és vágandó anyagok"
        assert message.to == [django_settings.WEEKLY_TASK_EMAIL]
        assert message.reply_to == [django_settings.WEEKLY_TASK_EMAIL]

    def test_unfinished_requests(self, production_manager, video_request):
        email_production_manager_unfinished_requests([video_request])

        message = only_message()
        assert message.subject == "Lezáratlan anyagok"
        assert message.to == [production_manager.email]

    def test_overdue_request(self, editor_in_chief, production_manager, video_request):
        email_responsible_overdue_request(video_request)

        message = only_message()
        assert message.subject == "Test Request | Lejárt határidejű felkérés"
        assert message.to == [video_request.responsible.email]
        assert set(message.cc) == {editor_in_chief.email, production_manager.email}


@pytest.mark.parametrize(
    "send_email",
    [email_user_new_comment, email_crew_new_comment],
    ids=["requester", "crew"],
)
def test_an_inline_avatar_falls_back_to_the_default(crew, send_email, video_request):
    author = make_user(
        avatar={
            "provider": "microsoft-graph",
            "microsoft-graph": "data:image/jpg;base64,/9j/4AAQ",
        }
    )
    comment = baker.make("video_requests.Comment", request=video_request, author=author)

    send_email(comment.id)

    html = only_message().alternatives[0].content
    assert "data:image" not in html
    assert "images/default_avatar." in html
