"""The four cron commands that mail the studio.

Each is checked for which rows it picks, and for reporting an empty run on stdout
instead of mailing it. The builders are wrapped, not replaced, so the templates
still render.
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.conf import settings as django_settings
from django.core import mail
from django.core.management import call_command
from django.utils.timezone import localtime
from model_bakery import baker

from tests.factories import make_user
from video_requests.emails import (
    email_crew_daily_reminder,
    email_production_manager_unfinished_requests,
    email_staff_weekly_tasks,
)
from video_requests.models import Request, Video

pytestmark = [pytest.mark.django_db, pytest.mark.emails]

#: A Thursday, so "this week" has days on both sides of it.
TODAY = "2020-11-19 10:20:30 +0100"


def run(command):
    with StringIO() as out:
        call_command(command, stdout=out)
        return out.getvalue()


def make_request(start, status=Request.Statuses.REQUESTED, **kwargs):
    start = localtime().fromisoformat(start) if isinstance(start, str) else start
    return baker.make(
        "video_requests.Request",
        start_datetime=start,
        end_datetime=start + timedelta(days=1),
        status=status,
        **kwargs,
    )


class TestWeeklyTasks:
    """What the studio has to shoot this week, and what is waiting to be cut."""

    @pytest.fixture(autouse=True)
    def this_thursday(self, time_machine):
        time_machine.move_to(TODAY)

    @pytest.fixture
    def recording(self, requester, staff_user):
        """Requests to be shot: this week, and still only asked for or accepted."""
        included = [
            make_request("2020-11-16T04:16:13+01:00", requester=requester),
            make_request(
                "2020-11-21T21:41:57+01:00",
                Request.Statuses.ACCEPTED,
                requester=requester,
            ),
        ]
        baker.make("video_requests.CrewMember", request=included[0], member=staff_user)
        excluded = [
            make_request("2020-11-15T10:01:24+01:00", requester=requester),  # last week
            make_request("2020-11-24T17:22:05+01:00", requester=requester),  # next week
            make_request(  # this week, but already past shooting
                "2020-11-20T14:55:45+01:00",
                Request.Statuses.EDITED,
                requester=requester,
            ),
        ]
        return included, excluded

    @pytest.fixture
    def editing(self, requester, staff_user):
        """Shot material with nothing, or nothing finished, to show for it."""
        without_video = make_request(
            localtime(), Request.Statuses.RECORDED, requester=requester
        )
        with_unedited = make_request(
            localtime(), Request.Statuses.UPLOADED, requester=requester
        )
        unedited = [
            baker.make(
                "video_requests.Video",
                request=with_unedited,
                status=Video.Statuses.PENDING,
            ),
            baker.make(
                "video_requests.Video",
                request=with_unedited,
                status=Video.Statuses.IN_PROGRESS,
                editor=staff_user,
            ),
        ]

        already_edited_request = make_request(
            localtime(), Request.Statuses.RECORDED, requester=requester
        )
        excluded_videos = [
            baker.make(
                "video_requests.Video",
                request=already_edited_request,
                status=Video.Statuses.EDITED,
            ),
            baker.make(  # good video status, but the request has moved on
                "video_requests.Video",
                request=make_request(
                    localtime(), Request.Statuses.EDITED, requester=requester
                ),
                status=Video.Statuses.PENDING,
            ),
        ]
        return without_video, with_unedited, unedited, excluded_videos

    def test_it_reports_the_week_and_mails_the_digest(self, editing, recording):
        included, excluded = recording
        without_video, with_unedited, unedited, excluded_videos = editing

        with patch(
            "video_requests.emails.email_staff_weekly_tasks",
            wraps=email_staff_weekly_tasks,
        ) as send:
            assert run("email_weekly_tasks") == (
                "Weekly tasks email was sent successfully.\n"
            )

        send.assert_called_once()
        to_record, to_start, to_finish = send.call_args.args

        assert list(to_record) == included
        assert not any(video_request in to_record for video_request in excluded)

        assert list(to_start) == [without_video]
        assert with_unedited not in to_start

        assert set(to_finish) == set(unedited)
        assert not any(video in to_finish for video in excluded_videos)

        assert len(mail.outbox) == 1
        assert django_settings.WEEKLY_TASK_EMAIL in mail.outbox[0].to
        assert mail.outbox[0].subject == "E heti forgatások és vágandó anyagok"

    def test_a_quiet_week_is_reported_instead_of_mailed(
        self, editing, recording, time_machine
    ):
        without_video, with_unedited, _, _ = editing
        without_video.status = Request.Statuses.EDITED
        without_video.save()
        with_unedited.status = Request.Statuses.ARCHIVED
        with_unedited.save()

        time_machine.move_to("2020-12-21 10:20:30 +0100")

        assert run("email_weekly_tasks") == "No tasks for this week.\n"
        assert not mail.outbox


class TestDailyReminders:

    @pytest.fixture(autouse=True)
    def today(self, time_machine):
        time_machine.move_to(TODAY)

    @pytest.fixture
    def shoots(self, editor_in_chief, requester, staff_user):
        with_crew = make_request("2020-11-19T18:00:00+01:00", requester=requester)
        without_crew = make_request("2020-11-19T20:00:00+01:00", requester=requester)
        crew = [
            baker.make(
                "video_requests.CrewMember", request=with_crew, member=staff_user
            ),
            baker.make(
                "video_requests.CrewMember", request=with_crew, member=editor_in_chief
            ),
        ]
        return with_crew, without_crew, crew

    def test_it_reminds_only_the_requests_that_have_a_crew(self, shoots):
        with_crew, without_crew, crew = shoots

        with patch(
            "video_requests.emails.email_crew_daily_reminder",
            wraps=email_crew_daily_reminder,
        ) as send:
            assert run("email_daily_reminders") == (
                "1 reminders were sent to crew members. There are 2 request(s) today.\n"
            )

        send.assert_called_once()
        assert send.call_args.args[0] == with_crew
        assert send.call_args.args[0] != without_crew
        assert set(send.call_args.args[1]) == set(crew)

        assert len(mail.outbox) == 1
        for member in crew:
            assert member.member.email in mail.outbox[0].to
        assert (
            mail.outbox[0].subject == f"Emlékeztető | {with_crew.title} | Mai forgatás"
        )

    def test_a_day_with_nothing_on_is_reported_instead(self, shoots, time_machine):
        time_machine.move_to("2020-11-20 10:20:30 +0100")

        assert run("email_daily_reminders") == "No reminders for today.\n"
        assert not mail.outbox


class TestUnfinishedRequests:
    """Material that is cut but not closed, nagged about weekly."""

    @pytest.fixture
    def requests(self, requester):
        included = [
            make_request(localtime(), Request.Statuses.EDITED, requester=requester),
            make_request(localtime(), Request.Statuses.ARCHIVED, requester=requester),
        ]
        excluded = [
            make_request(localtime(), Request.Statuses.ACCEPTED, requester=requester),
            make_request(localtime(), Request.Statuses.UPLOADED, requester=requester),
            make_request(localtime(), Request.Statuses.DONE, requester=requester),
        ]
        return included, excluded

    def test_it_lists_them_for_the_production_manager(
        self, production_manager, requests
    ):
        included, excluded = requests

        with patch(
            "video_requests.emails.email_production_manager_unfinished_requests",
            wraps=email_production_manager_unfinished_requests,
        ) as send:
            assert run("email_unfinished_requests") == (
                "Unfinished requests email was sent successfully.\n"
            )

        send.assert_called_once()
        listed = send.call_args.args[0]
        assert set(listed) == set(included)
        assert not any(video_request in listed for video_request in excluded)

        assert len(mail.outbox) == 1
        assert production_manager.email in mail.outbox[0].to
        assert mail.outbox[0].subject == "Lezáratlan anyagok"

    def test_nothing_unfinished_is_reported_instead_of_mailed(
        self, production_manager, requests
    ):
        included, _ = requests
        for video_request in included:
            video_request.delete()

        with patch(
            "video_requests.emails.email_production_manager_unfinished_requests",
            wraps=email_production_manager_unfinished_requests,
        ) as send:
            assert run("email_unfinished_requests") == "All requests are finished.\n"

        send.assert_not_called()
        assert not mail.outbox


def mentioned(message, requests):
    """Titles of ``requests`` found in the plain-text body, in the order they appear."""
    found = [
        video_request
        for video_request in requests
        if video_request.title in message.body
    ]
    return [
        video_request.title
        for video_request in sorted(found, key=lambda r: message.body.index(r.title))
    ]


def sent_with(subject):
    return [message for message in mail.outbox if message.subject == subject]


class TestOverdueRequests:
    """A weekly digest of shot requests whose videos missed the deadline."""

    @pytest.fixture(autouse=True)
    def today(self, time_machine):
        time_machine.move_to(TODAY)

    @pytest.fixture
    def responsibles(self, staff_user):
        return staff_user, make_user(is_staff=True)

    @pytest.fixture
    def overdue(self, requester, responsibles):
        """In deadline order; the deadline is three weeks after the event ends."""
        first, second = responsibles
        return [
            make_request(
                "2020-09-29T15:30:00+01:00",
                Request.Statuses.UPLOADED,
                requester=requester,
                responsible=first,
            ),
            make_request(
                "2020-10-05T18:00:00+01:00",
                Request.Statuses.RECORDED,
                requester=requester,
                responsible=second,
            ),
            make_request(
                "2020-10-12T18:00:00+01:00",
                Request.Statuses.RECORDED,
                requester=requester,
                responsible=first,
            ),
            make_request(
                "2020-10-14T18:00:00+01:00",
                Request.Statuses.UPLOADED,
                requester=requester,
            ),
        ]

    @pytest.fixture
    def not_overdue(self, requester, staff_user):
        return [
            # Never shot, so not a video that is late.
            make_request(
                "2020-09-29T15:30:00+01:00",
                Request.Statuses.REQUESTED,
                requester=requester,
                responsible=staff_user,
            ),
            make_request(
                "2020-09-29T15:30:00+01:00",
                Request.Statuses.ACCEPTED,
                requester=requester,
                responsible=staff_user,
            ),
            # Already cut.
            make_request(
                "2020-09-29T15:30:00+01:00",
                Request.Statuses.EDITED,
                requester=requester,
                responsible=staff_user,
            ),
            # Still within its deadline.
            make_request(
                "2020-11-05T21:00:00+01:00",
                Request.Statuses.UPLOADED,
                requester=requester,
                responsible=staff_user,
            ),
        ]

    def test_each_responsible_gets_one_digest_of_their_own_requests(
        self, overdue, not_overdue, responsibles
    ):
        assert run("email_overdue_requests") == (
            "Overdue requests emails were sent: 4 requests, 2 responsibles.\n"
        )

        first, second = responsibles
        digests = {
            tuple(message.to): message
            for message in sent_with("Lejárt határidejű felkéréseid")
        }
        assert digests.keys() == {(first.email,), (second.email,)}
        assert not any(message.cc for message in digests.values())
        everything = overdue + not_overdue
        assert mentioned(digests[(first.email,)], everything) == [
            overdue[0].title,
            overdue[2].title,
        ]
        assert mentioned(digests[(second.email,)], everything) == [overdue[1].title]
        assert "Határidő: 2020. okt. 21. (29 napja lejárt)" in (
            digests[(first.email,)].body
        )

    def test_the_editor_in_chief_and_production_managers_get_one_summary(
        self, editor_in_chief, production_manager, overdue, not_overdue
    ):
        run("email_overdue_requests")

        (summary,) = sent_with("Lejárt határidejű felkérések")
        assert set(summary.to) == {editor_in_chief.email, production_manager.email}
        assert not summary.cc
        assert mentioned(summary, overdue + not_overdue) == [
            video_request.title for video_request in overdue
        ]
        assert "Felelős: nincs" in summary.body

    def test_a_responsible_outside_the_studio_gets_no_digest(
        self, editor_in_chief, requester
    ):
        outsider = make_user()
        make_request(
            "2020-10-05T18:00:00+01:00",
            Request.Statuses.RECORDED,
            requester=requester,
            responsible=outsider,
        )

        run("email_overdue_requests")

        assert not sent_with("Lejárt határidejű felkéréseid")
        assert len(sent_with("Lejárt határidejű felkérések")) == 1

    def test_nothing_overdue_is_reported_instead_of_mailed(self, not_overdue):
        assert run("email_overdue_requests") == "No overdue request was found.\n"

        assert not mail.outbox
