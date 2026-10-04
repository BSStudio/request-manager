"""Which API action sends which notification, and to whom it must not go.

Templates and recipient lists are tested on the builders themselves, in
tests/unit/video_requests/emails_tests.py.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings as django_settings
from django.core import mail
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from common.models import User, get_system_user
from tests.api.helpers import login
from tests.factories import make_user
from video_requests.models import Request, Todo, Video

pytestmark = [pytest.mark.django_db, pytest.mark.emails]


@pytest.fixture(autouse=True)
def run_tasks_eagerly(settings):
    """The notifications are Celery tasks; run them inline."""
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture
def request_data():
    return {
        "title": "Test Request",
        "start_datetime": localtime() + timedelta(minutes=10),
        "end_datetime": localtime() + timedelta(days=1),
        "place": "Test place",
        "type": "Test type",
    }


class TestNewRequestConfirmation:

    def test_a_requester_who_is_logged_in_is_confirmed(
        self, api_client, basic_user, editor_in_chief, request_data
    ):
        login(api_client, basic_user)

        response = api_client.post(
            reverse("api:v1:requests:request-list"), request_data
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert basic_user.email in mail.outbox[0].to
        assert editor_in_chief.email in mail.outbox[0].bcc
        assert django_settings.DEFAULT_REPLY_EMAIL in mail.outbox[0].reply_to
        assert (
            mail.outbox[0].subject
            == f"{request_data['title']} | Forgatási felkérésedet fogadtuk"
        )

    def test_staff_filing_on_the_admin_endpoint_must_ask_for_it(
        self, api_client, editor_in_chief, request_data, staff_user
    ):
        login(api_client, staff_user)

        response = api_client.post(
            reverse("api:v1:admin:requests:request-list"),
            request_data | {"send_notification": True},
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert staff_user.email in mail.outbox[0].to
        assert editor_in_chief.email in mail.outbox[0].bcc

    def test_an_anonymous_requester_is_confirmed_at_the_address_they_gave(
        self, api_client, editor_in_chief, request_data, settings
    ):
        settings.TURNSTILE_TESTING_PASS = True

        response = api_client.post(
            reverse("api:v1:requests:request-list"),
            request_data
            | {
                "requester_first_name": "Test",
                "requester_last_name": "User",
                "requester_email": "test.user@example.com",
                "requester_mobile": "+36509999999",
                "comment": "Additional information",
                "captcha": "randomCaptchaResponseToken",
            },
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert "test.user@example.com" in mail.outbox[0].to
        assert editor_in_chief.email in mail.outbox[0].bcc


class TestVideoPublished:
    """Publishing opens a sharing task, and invites the requester to watch."""

    @pytest.fixture
    def requester(self, requester_is_staff):
        return make_user(is_staff=requester_is_staff)

    @pytest.fixture
    def video(self, requester):
        video_request = baker.make(
            "video_requests.Request",
            requester=requester,
            start_datetime=localtime() - timedelta(days=3),
            end_datetime=localtime() - timedelta(days=2),
            status=Request.Statuses.UPLOADED,
            additional_data={"accepted": True, "recording": {"path": "test/path"}},
        )
        return baker.make(
            "video_requests.Video",
            request=video_request,
            status=Video.Statuses.PENDING,
        )

    @staticmethod
    def publish(api_client, video, url_only=False, **additional_data):
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": video.request.id, "pk": video.id},
        )
        return url if url_only else api_client.patch(url, additional_data)

    @pytest.mark.parametrize(
        "requester_is_staff",
        [False, True],
        ids=["outside_requester", "staff_requester"],
    )
    def test_the_requester_is_invited_unless_they_are_staff(
        self,
        api_client,
        pr_responsible,
        requester,
        requester_is_staff,
        staff_user,
        video,
    ):
        login(api_client, staff_user)
        url = self.publish(api_client, video, url_only=True)

        response = api_client.patch(
            url,
            {
                "editor": staff_user.id,
                "additional_data": {
                    "editing_done": True,
                    "coding": {"website": True},
                    "publishing": {"website": "https://example.com"},
                },
            },
            format="json",
        )

        assert response.status_code == HTTP_200_OK
        assert response.data["status"] == Video.Statuses.PUBLISHED

        todo = Todo.objects.get(video=video)
        assert todo.creator == get_system_user()
        assert todo.description == "Megosztás közösségi platformokon"
        assert todo.assignees.contains(pr_responsible)

        assert pr_responsible.email in mail.outbox[0].to
        assert mail.outbox[0].subject == "Feladatot rendeltek hozzád"

        if requester_is_staff:
            # Staff watch their own work; only the sharing task goes out.
            assert len(mail.outbox) == 1
        else:
            assert len(mail.outbox) == 2
            assert requester.email in mail.outbox[1].to
            assert django_settings.DEFAULT_REPLY_EMAIL in mail.outbox[1].reply_to
            assert (
                mail.outbox[1].subject
                == f"{video.request.title} | Új videót publikáltunk"
            )

    @pytest.mark.parametrize(
        "requester_is_staff",
        [False, True],
        ids=["outside_requester", "staff_requester"],
    )
    def test_republishing_neither_re_invites_nor_re_opens_the_task(
        self, api_client, pr_responsible, requester_is_staff, staff_user, video
    ):
        login(api_client, staff_user)
        url = self.publish(api_client, video, url_only=True)
        api_client.patch(
            url,
            {
                "editor": staff_user.id,
                "additional_data": {
                    "editing_done": True,
                    "coding": {"website": True},
                    "publishing": {"website": "https://example.com"},
                },
            },
            format="json",
        )
        sent = len(mail.outbox)

        # Unpublish, then publish somewhere else.
        response = api_client.patch(
            url, {"additional_data": {"publishing": {"website": ""}}}, format="json"
        )
        assert response.data["status"] == Video.Statuses.CODED
        response = api_client.patch(
            url,
            {"additional_data": {"publishing": {"website": "https://example123.com"}}},
            format="json",
        )
        assert response.data["status"] == Video.Statuses.PUBLISHED

        assert Todo.objects.filter(video=video).count() == 1
        assert len(mail.outbox) == sent


class TestTodoAssignment:
    """Only people newly put on a task hear about it, and only staff."""

    @pytest.fixture
    def video_request(self):
        return baker.make("video_requests.Request")

    def assignees(self, quantity, is_staff=True):
        return baker.make(
            User, is_staff=is_staff, _fill_optional=True, _quantity=quantity
        )

    @pytest.mark.parametrize("on_a_video", [False, True], ids=["request", "video"])
    def test_creating_a_todo_tells_its_assignees(
        self, api_client, on_a_video, staff_user, video_request
    ):
        login(api_client, staff_user)
        users = self.assignees(5)

        if on_a_video:
            video = baker.make("video_requests.Video", request=video_request)
            url = reverse(
                "api:v1:admin:requests:request:video:todo-list",
                kwargs={"request_pk": video_request.id, "video_pk": video.id},
            )
        else:
            url = reverse(
                "api:v1:admin:requests:request:todo-list",
                kwargs={"request_pk": video_request.id},
            )

        response = api_client.post(
            url,
            {
                "assignees": [user.id for user in users],
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing.",
                "status": Todo.Statuses.CLOSED,
            },
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email for user in users]
        assert mail.outbox[0].subject == "Feladatot rendeltek hozzád"

    def test_adding_assignees_only_tells_the_new_ones(
        self, api_client, staff_user, video_request
    ):
        existing = self.assignees(2)
        new = self.assignees(3)
        todo = baker.make(
            "video_requests.Todo", assignees=existing, request=video_request
        )
        login(api_client, staff_user)

        response = api_client.patch(
            reverse("api:v1:admin:todos:todo-detail", kwargs={"pk": todo.id}),
            {"assignees": [user.id for user in new + existing]},
        )

        assert response.status_code == HTTP_200_OK
        # The first mail went out when the to-do itself was created.
        assert len(mail.outbox) == 2
        assert mail.outbox[1].to == [user.email for user in new]
        assert mail.outbox[1].subject == "Feladatot rendeltek hozzád"

    def test_removing_an_assignee_tells_nobody(
        self, api_client, staff_user, video_request
    ):
        existing = self.assignees(3)
        todo = baker.make(
            "video_requests.Todo", assignees=existing, request=video_request
        )
        login(api_client, staff_user)

        response = api_client.patch(
            reverse("api:v1:admin:todos:todo-detail", kwargs={"pk": todo.id}),
            {"assignees": [existing[0].id]},
        )

        assert response.status_code == HTTP_200_OK
        assert len(mail.outbox) == 1

    def test_assignees_who_are_not_staff_are_never_told(
        self, api_client, staff_user, video_request
    ):
        existing = self.assignees(2, is_staff=False)
        new = self.assignees(3, is_staff=False)
        todo = baker.make(
            "video_requests.Todo", assignees=existing, request=video_request
        )
        login(api_client, staff_user)

        response = api_client.patch(
            reverse("api:v1:admin:todos:todo-detail", kwargs={"pk": todo.id}),
            {"assignees": [user.id for user in new + existing]},
        )

        assert response.status_code == HTTP_200_OK
        assert len(mail.outbox) == 0


class TestNewComment:
    @pytest.fixture
    def crewed_request(self, requester):
        video_request = baker.make(
            "video_requests.Request",
            requester=requester,
            responsible=make_user(is_staff=True),
        )
        baker.make(
            "video_requests.CrewMember",
            request=video_request,
            member=make_user(is_staff=True),
            _quantity=2,
        )
        return video_request

    @staticmethod
    def crew_emails(video_request):
        return [member.member.email for member in video_request.crew.all()]

    def test_a_public_comment_reaches_the_requester_and_the_crew(
        self, api_client, crewed_request, editor_in_chief, requester, staff_user
    ):
        login(api_client, staff_user)

        response = api_client.post(
            reverse(
                "api:v1:admin:requests:request:comment-list",
                kwargs={"request_pk": crewed_request.id},
            ),
            {"text": "Lorem ipsum dolor sit amet.", "internal": False},
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 2

        to_requester, to_crew = mail.outbox
        assert requester.email in to_requester.to
        assert django_settings.DEFAULT_REPLY_EMAIL in to_requester.reply_to
        assert to_requester.subject == f"{crewed_request.title} | Új üzenet a BSS-től"

        for email in self.crew_emails(crewed_request):
            assert email in to_crew.to
        assert crewed_request.responsible.email in to_crew.cc
        assert editor_in_chief.email in to_crew.cc

        # Both templates show the commenter's avatar.
        for message in mail.outbox:
            assert staff_user.avatar_url in message.alternatives[0].content

    def test_an_internal_comment_never_reaches_the_requester(
        self, api_client, crewed_request, editor_in_chief, requester, staff_user
    ):
        login(api_client, staff_user)

        response = api_client.post(
            reverse(
                "api:v1:admin:requests:request:comment-list",
                kwargs={"request_pk": crewed_request.id},
            ),
            {"text": "New comment", "internal": True},
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert not self.addressed(mail.outbox[0], requester.email)
        for email in self.crew_emails(crewed_request):
            assert email in mail.outbox[0].to
        assert crewed_request.responsible.email in mail.outbox[0].cc
        assert editor_in_chief.email in mail.outbox[0].cc

    def test_a_banned_requester_is_never_written_to(
        self, api_client, editor_in_chief, staff_user
    ):
        banned_user = make_user(banned=True)
        video_request = baker.make("video_requests.Request", requester=banned_user)
        login(api_client, staff_user)

        response = api_client.post(
            reverse(
                "api:v1:admin:requests:request:comment-list",
                kwargs={"request_pk": video_request.id},
            ),
            {"text": "New comment", "internal": False},
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert not self.addressed(mail.outbox[0], banned_user.email)

    def test_the_requester_commenting_only_notifies_the_crew(
        self, api_client, crewed_request, editor_in_chief, requester
    ):
        login(api_client, requester)

        response = api_client.post(
            reverse(
                "api:v1:requests:request:comment-list",
                kwargs={"request_pk": crewed_request.id},
            ),
            {"text": "New comment"},
        )

        assert response.status_code == HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert not self.addressed(mail.outbox[0], requester.email)
        for email in self.crew_emails(crewed_request):
            assert email in mail.outbox[0].to
        assert crewed_request.responsible.email in mail.outbox[0].cc
        assert editor_in_chief.email in mail.outbox[0].cc

    @staticmethod
    def addressed(message, address):
        return address in message.to + message.cc + message.bcc


class TestRequestModified:
    """The crew is told what changed, and only when somebody asks for it."""

    @pytest.fixture
    def video_request(self, requester):
        return baker.make(
            "video_requests.Request",
            requester=requester,
            responsible=make_user(is_staff=True),
        )

    @pytest.fixture
    def crewed_request(self, video_request):
        baker.make(
            "video_requests.CrewMember",
            request=video_request,
            member=make_user(is_staff=True),
            _quantity=2,
        )
        return video_request

    @staticmethod
    def url(video_request):
        return reverse(
            "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
        )

    def test_the_crew_is_told_when_the_notification_box_is_ticked(
        self, api_client, crewed_request, editor_in_chief, staff_user
    ):
        login(api_client, staff_user)

        response = api_client.patch(
            self.url(crewed_request),
            {
                "title": "Test Request Modified",
                "start_datetime": localtime() + timedelta(minutes=10),
                "end_datetime": localtime() + timedelta(days=3),
                "place": "New place",
                "type": "New type",
                "send_notification": True,
            },
        )

        assert response.status_code == HTTP_200_OK
        assert len(mail.outbox) == 1
        for member in crewed_request.crew.all():
            assert member.member.email in mail.outbox[0].to
        assert crewed_request.responsible.email in mail.outbox[0].cc
        assert editor_in_chief.email in mail.outbox[0].cc
        assert mail.outbox[0].subject == "Test Request Modified | Felkérés módosítva"


class TestWhichChangesAreWorthAnEmail:
    """Only the fields the crew has to act on count as a change."""

    @pytest.fixture
    def notify(self):
        with patch("video_requests.emails.email_crew_request_modified.delay") as delay:
            yield delay

    @pytest.fixture
    def video_request(self, api_client, requester, staff_user):
        login(api_client, staff_user)
        return baker.make("video_requests.Request", requester=requester)

    @staticmethod
    def url(video_request):
        return reverse(
            "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
        )

    def test_a_deadline_change_alone_is_not_worth_one(
        self, api_client, notify, video_request
    ):
        response = api_client.patch(
            self.url(video_request),
            {
                "deadline": (video_request.end_datetime + timedelta(weeks=1)).date(),
                "send_notification": True,
            },
        )

        assert response.status_code == HTTP_200_OK
        notify.assert_not_called()

    def test_a_title_change_is_reported_with_both_values(
        self, api_client, notify, staff_user, video_request
    ):
        response = api_client.patch(
            self.url(video_request), {"title": "TC1", "send_notification": True}
        )

        assert response.status_code == HTTP_200_OK
        notify.assert_called_once()
        assert notify.call_args.args[0] == video_request.id
        assert notify.call_args.args[1] == staff_user.get_full_name_eastern_order()
        assert notify.call_args.args[3] == [
            {
                "name": "Esemény neve",
                "next": "TC1",
                "previous": video_request.title,
            }
        ]

    def test_a_deadline_riding_along_with_a_title_is_left_out(
        self, api_client, notify, video_request
    ):
        response = api_client.patch(
            self.url(video_request),
            {
                "title": "TC2",
                "deadline": (video_request.end_datetime + timedelta(weeks=2)).date(),
                "send_notification": True,
            },
        )

        assert response.status_code == HTTP_200_OK
        notify.assert_called_once()
        assert [change["name"] for change in notify.call_args.args[3]] == [
            "Esemény neve"
        ]

    def test_every_field_the_crew_cares_about_is_reported_in_order(
        self, api_client, notify, video_request
    ):
        data = {
            "title": "TC3",
            "start_datetime": video_request.start_datetime + timedelta(minutes=5),
            "end_datetime": video_request.end_datetime + timedelta(minutes=5),
            "place": "TC3 - Place",
            "type": "TC3 - Type",
            "send_notification": True,
        }

        response = api_client.patch(self.url(video_request), data)

        assert response.status_code == HTTP_200_OK
        notify.assert_called_once()
        assert notify.call_args.args[3] == [
            {
                "name": "Esemény neve",
                "next": data["title"],
                "previous": video_request.title,
            },
            {
                "name": "Esemény kezdésének ideje",
                "next": data["start_datetime"],
                "previous": video_request.start_datetime,
            },
            {
                "name": "Esemény várható befejezése",
                "next": data["end_datetime"],
                "previous": video_request.end_datetime,
            },
            {
                "name": "Helyszín",
                "next": data["place"],
                "previous": video_request.place,
            },
            {
                "name": "Videó típusa",
                "next": data["type"],
                "previous": video_request.type,
            },
        ]
