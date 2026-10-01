"""``update_request_status`` rule by rule.

The status is derived, never set directly: ``additional_data`` and the request's
videos move it.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils.timezone import localtime
from model_bakery import baker

from video_requests.models import Request, Video
from video_requests.utilities import update_request_status

pytestmark = pytest.mark.django_db


def make_request(*, additional_data=None, past=False, **kwargs):
    """A request whose event is either still ahead of us or already over."""
    end = localtime() - timedelta(days=1) if past else localtime() + timedelta(days=1)
    return baker.make(
        "video_requests.Request",
        additional_data=additional_data or {},
        start_datetime=end - timedelta(hours=2),
        end_datetime=end,
        **kwargs,
    )


def recorded_request(**additional_data):
    """A request past its event with a recording path, so at least UPLOADED."""
    return make_request(
        past=True,
        additional_data={"accepted": True, "recording": {"path": "N:/test"}}
        | additional_data,
    )


def edited_video(video_request, status=Video.Statuses.EDITED):
    """A video pinned to a status, so the cascade cannot move it around."""
    return baker.make(
        "video_requests.Video",
        request=video_request,
        status=status,
        additional_data={"status_by_admin": {"status": status}},
    )


class TestStatusSetByAdmin:
    def test_an_admin_set_status_wins_over_every_other_rule(self):
        # Everything else here says DENIED.
        video_request = make_request(
            additional_data={
                "accepted": False,
                "status_by_admin": {"status": Request.Statuses.ARCHIVED},
            }
        )

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.ARCHIVED

    def test_a_status_by_admin_without_a_status_does_not_win(self):
        # Clearing the status hands the request back to the derived flow.
        video_request = make_request(
            additional_data={
                "accepted": True,
                "status_by_admin": {"admin_id": 1, "admin_name": "Someone"},
            }
        )

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.ACCEPTED

    def test_a_null_status_by_admin_status_does_not_win(self):
        video_request = make_request(
            additional_data={"accepted": True, "status_by_admin": {"status": None}}
        )

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.ACCEPTED


class TestDerivedStatus:
    def test_a_request_nobody_has_answered_stays_requested(self):
        video_request = make_request()

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.REQUESTED

    @pytest.mark.parametrize(
        "accepted,expected",
        [
            (True, Request.Statuses.ACCEPTED),
            (False, Request.Statuses.DENIED),
        ],
    )
    def test_the_answer_decides_between_accepted_and_denied(self, accepted, expected):
        video_request = make_request(additional_data={"accepted": accepted})

        update_request_status(video_request)

        assert video_request.status == expected

    @pytest.mark.parametrize(
        "field,value,expected",
        [
            ("canceled", True, Request.Statuses.CANCELED),
            ("canceled", False, Request.Statuses.ACCEPTED),
            ("failed", True, Request.Statuses.FAILED),
            ("failed", False, Request.Statuses.ACCEPTED),
        ],
    )
    def test_cancelling_and_failing_apply_to_an_accepted_request(
        self, field, value, expected
    ):
        video_request = make_request(additional_data={"accepted": True, field: value})

        update_request_status(video_request)

        assert video_request.status == expected

    @pytest.mark.parametrize("field", ["canceled", "failed"])
    def test_a_denied_request_is_not_cancelled_or_failed(self, field):
        video_request = make_request(additional_data={"accepted": False, field: True})

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.DENIED

    def test_the_event_being_over_makes_it_recorded(self):
        video_request = make_request(past=True, additional_data={"accepted": True})

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.RECORDED

    def test_a_cancelled_request_does_not_become_recorded(self):
        video_request = make_request(
            past=True, additional_data={"accepted": True, "canceled": True}
        )

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.CANCELED

    def test_a_recording_path_makes_it_uploaded(self):
        video_request = recorded_request()

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.UPLOADED

    def test_an_empty_recording_path_leaves_it_recorded(self):
        video_request = make_request(
            past=True, additional_data={"accepted": True, "recording": {"path": ""}}
        )

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.RECORDED


class TestVideoDrivenStatus:
    def test_all_videos_edited_makes_the_request_edited(self):
        video_request = recorded_request()
        edited_video(video_request)
        edited_video(video_request)

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.EDITED

    def test_one_unedited_video_holds_the_request_at_uploaded(self):
        video_request = recorded_request()
        edited_video(video_request)
        baker.make(
            "video_requests.Video", request=video_request, status=Video.Statuses.PENDING
        )

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.UPLOADED

    def test_a_request_without_videos_stays_uploaded(self):
        video_request = recorded_request()

        update_request_status(video_request)

        assert video_request.status == Request.Statuses.UPLOADED

    @pytest.mark.parametrize(
        "copied_to_gdrive,expected",
        [
            (True, Request.Statuses.ARCHIVED),
            (False, Request.Statuses.EDITED),
        ],
    )
    def test_copying_the_raw_material_archives_the_request(
        self, copied_to_gdrive, expected
    ):
        video_request = recorded_request()
        video_request.additional_data["recording"][
            "copied_to_gdrive"
        ] = copied_to_gdrive
        edited_video(video_request, Video.Statuses.DONE)

        update_request_status(video_request)

        assert video_request.status == expected

    @pytest.mark.parametrize(
        "removed,expected",
        [
            (True, Request.Statuses.DONE),
            (False, Request.Statuses.ARCHIVED),
        ],
    )
    def test_removing_the_raw_material_closes_the_request(self, removed, expected):
        video_request = recorded_request()
        video_request.additional_data["recording"] |= {
            "copied_to_gdrive": True,
            "removed": removed,
        }
        edited_video(video_request, Video.Statuses.DONE)

        update_request_status(video_request)

        assert video_request.status == expected


class TestCascadeToVideos:
    """The recursion between a request and its videos, and the guard on it."""

    @staticmethod
    def uploaded_request_with_a_video():
        # status_by_admin keeps the derived rules — including the one that pushes
        # the status into the videos itself — out of the way.
        video_request = make_request(
            additional_data={"status_by_admin": {"status": Request.Statuses.UPLOADED}}
        )
        video = baker.make(
            "video_requests.Video",
            request=video_request,
            editor=video_request.requester,
            status=Video.Statuses.PENDING,
        )
        return video_request, video

    def test_the_videos_are_recalculated_too(self):
        video_request, video = self.uploaded_request_with_a_video()

        update_request_status(video_request)

        video.refresh_from_db()
        assert video.status == Video.Statuses.IN_PROGRESS

    def test_a_call_coming_from_a_video_does_not_cascade_back(self):
        video_request, video = self.uploaded_request_with_a_video()

        update_request_status(video_request, called_from_video=True)

        video.refresh_from_db()
        assert video.status == Video.Statuses.PENDING

    def test_reaching_uploaded_pushes_the_new_status_into_the_videos_regardless(self):
        # The recording-path rule hands its freshly computed status straight to
        # the videos, which is not the cascade and so is not guarded by it.
        video_request = recorded_request()
        video = baker.make(
            "video_requests.Video",
            request=video_request,
            editor=video_request.requester,
            status=Video.Statuses.PENDING,
        )

        update_request_status(video_request, called_from_video=True)

        video.refresh_from_db()
        assert video.status == Video.Statuses.IN_PROGRESS


class TestSchEventsNotification:
    """An externally submitted request has our answer pushed back to SCH events."""

    @pytest.fixture
    def notify(self):
        with patch(
            "video_requests.utilities.notify_sch_event_management_system.delay"
        ) as delay:
            yield delay

    @staticmethod
    def external(**additional_data):
        return make_request(
            additional_data={
                "external": {"sch_events_callback_url": "https://example.com/callback"}
            }
            | additional_data
        )

    def test_answering_a_fresh_external_request_notifies(self, notify):
        video_request = self.external(accepted=True)

        update_request_status(video_request)

        notify.assert_called_once_with(video_request.id)

    def test_turning_a_denial_into_an_acceptance_notifies(self, notify):
        video_request = self.external(accepted=True)
        video_request.status = Request.Statuses.DENIED
        video_request.save()

        update_request_status(video_request)

        notify.assert_called_once_with(video_request.id)

    def test_withdrawing_an_acceptance_notifies(self, notify):
        video_request = self.external(accepted=False)
        video_request.status = Request.Statuses.ACCEPTED
        video_request.save()

        update_request_status(video_request)

        notify.assert_called_once_with(video_request.id)

    def test_re_confirming_an_already_accepted_request_stays_quiet(self, notify):
        video_request = self.external(accepted=True)
        video_request.status = Request.Statuses.ACCEPTED
        video_request.save()

        update_request_status(video_request)

        notify.assert_not_called()

    def test_a_request_without_a_callback_url_is_never_pushed(self, notify):
        video_request = make_request(additional_data={"accepted": True})

        update_request_status(video_request)

        notify.assert_not_called()
