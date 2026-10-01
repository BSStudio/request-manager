"""``update_video_status`` rule by rule.

Reaching PUBLISHED has side effects: a social media to-do and an e-mail to the
requester.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils.timezone import localtime
from model_bakery import baker

from common.models import get_system_user
from tests.factories import make_user
from video_requests.models import Request, Todo, Video
from video_requests.utilities import update_video_status

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def published_email():
    """Every PUBLISHED transition tries to send this; tests opt in to asserting."""
    with patch("video_requests.utilities.email_user_video_published.delay") as delay:
        yield delay


def make_video(*, request_status=Request.Statuses.UPLOADED, editor=True, **kwargs):
    start = localtime() - timedelta(days=2)
    video_request = baker.make(
        "video_requests.Request",
        start_datetime=start,
        end_datetime=start + timedelta(hours=2),
        status=request_status,
        # status_by_admin keeps the request's own rules from moving it back when
        # the cascade reaches it.
        additional_data={"status_by_admin": {"status": request_status}},
    )
    return baker.make(
        "video_requests.Video",
        request=video_request,
        editor=video_request.requester if editor else None,
        additional_data=kwargs.pop("additional_data", {}),
        **kwargs,
    )


EDITED_DATA = {"editing_done": True}
CODED_DATA = EDITED_DATA | {"coding": {"website": True}}
PUBLISHED_DATA = CODED_DATA | {"publishing": {"website": "https://example.com"}}


class TestStatusSetByAdmin:
    def test_an_admin_set_status_wins_over_every_other_rule(self):
        # No editor, no editing: the derived flow would say PENDING.
        video = make_video(
            editor=False,
            additional_data={"status_by_admin": {"status": Video.Statuses.DONE}},
        )

        update_video_status(video)

        assert video.status == Video.Statuses.DONE

    def test_a_null_status_by_admin_status_does_not_win(self):
        video = make_video(
            additional_data={"status_by_admin": {"status": None}} | EDITED_DATA
        )

        update_video_status(video)

        assert video.status == Video.Statuses.EDITED


class TestDerivedStatus:
    def test_a_video_without_an_editor_stays_pending(self):
        video = make_video(editor=False)

        update_video_status(video)

        assert video.status == Video.Statuses.PENDING

    def test_an_editor_on_an_uploaded_request_starts_the_work(self):
        video = make_video()

        update_video_status(video)

        assert video.status == Video.Statuses.IN_PROGRESS

    def test_an_editor_before_the_material_is_uploaded_is_not_enough(self):
        video = make_video(request_status=Request.Statuses.ACCEPTED)

        update_video_status(video)

        assert video.status == Video.Statuses.PENDING

    def test_the_request_status_may_be_handed_in_before_it_is_saved(self):
        # This is how update_request_status passes down the status it just
        # computed, which is not on the request yet.
        video = make_video(request_status=Request.Statuses.ACCEPTED)

        update_video_status(
            video, called_from_request=True, request_status=Request.Statuses.UPLOADED
        )

        assert video.status == Video.Statuses.IN_PROGRESS

    @pytest.mark.parametrize(
        "editing_done,expected",
        [(True, Video.Statuses.EDITED), (False, Video.Statuses.IN_PROGRESS)],
    )
    def test_finishing_the_edit_makes_it_edited(self, editing_done, expected):
        video = make_video(additional_data={"editing_done": editing_done})

        update_video_status(video)

        assert video.status == expected

    @pytest.mark.parametrize(
        "website,expected",
        [(True, Video.Statuses.CODED), (False, Video.Statuses.EDITED)],
    )
    def test_coding_for_the_website_makes_it_coded(self, website, expected):
        video = make_video(
            additional_data=EDITED_DATA | {"coding": {"website": website}}
        )

        update_video_status(video)

        assert video.status == expected

    def test_a_publishing_url_makes_it_published(self):
        video = make_video(additional_data=PUBLISHED_DATA)

        update_video_status(video)

        assert video.status == Video.Statuses.PUBLISHED

    def test_an_empty_publishing_url_leaves_it_coded(self):
        video = make_video(additional_data=CODED_DATA | {"publishing": {"website": ""}})

        update_video_status(video)

        assert video.status == Video.Statuses.CODED

    @pytest.mark.parametrize(
        "hq_archive,expected",
        [(True, Video.Statuses.DONE), (False, Video.Statuses.PUBLISHED)],
    )
    def test_archiving_the_hq_export_closes_the_video(self, hq_archive, expected):
        video = make_video(
            additional_data=PUBLISHED_DATA | {"archiving": {"hq_archive": hq_archive}}
        )

        update_video_status(video)

        assert video.status == expected


class TestPublishingSideEffects:
    """Only the transition into PUBLISHED fires these, and only once."""

    def test_publishing_opens_a_social_media_todo_for_the_pr_responsible(self):
        pr_responsible = make_user(is_staff=True, groups=("PR felelős",))
        video = make_video(additional_data=PUBLISHED_DATA)

        update_video_status(video)

        todo = Todo.objects.get(video=video, creator=get_system_user())
        assert todo.description == "Megosztás közösségi platformokon"
        assert todo.request == video.request
        assert list(todo.assignees.all()) == [pr_responsible]

    def test_a_video_already_published_does_not_get_a_second_todo(self):
        video = make_video(
            status=Video.Statuses.PUBLISHED, additional_data=PUBLISHED_DATA
        )

        update_video_status(video)

        assert not Todo.objects.filter(video=video).exists()

    def test_re_running_the_transition_reuses_the_existing_todo(self):
        video = make_video(additional_data=PUBLISHED_DATA)

        update_video_status(video)
        video.status = Video.Statuses.CODED
        video.save()
        update_video_status(video)

        assert Todo.objects.filter(video=video, creator=get_system_user()).count() == 1

    def test_publishing_invites_the_requester_to_watch_and_rate(self, published_email):
        video = make_video(additional_data=PUBLISHED_DATA)

        update_video_status(video)

        published_email.assert_called_once_with(video.id)

    def test_the_requester_is_not_invited_twice(self, published_email):
        video = make_video(
            additional_data=CODED_DATA
            | {
                "publishing": {
                    "website": "https://example.com",
                    "email_sent_to_user": True,
                }
            }
        )

        update_video_status(video)

        published_email.assert_not_called()

    def test_a_staff_requester_is_not_invited(self, published_email):
        video = make_video(additional_data=PUBLISHED_DATA)
        video.request.requester.is_staff = True
        video.request.requester.save()

        update_video_status(video)

        published_email.assert_not_called()


class TestCascadeToTheRequest:
    def test_the_request_is_recalculated_too(self):
        video = make_video(additional_data=PUBLISHED_DATA)
        # Drop the pin so the request recomputes from its own data.
        video.request.additional_data = {
            "accepted": True,
            "recording": {"path": "N:/test", "copied_to_gdrive": True},
        }
        video.request.save()

        update_video_status(video)

        video.request.refresh_from_db()
        # One published video is not DONE, so the request stops at EDITED.
        assert video.request.status == Request.Statuses.EDITED

    def test_a_call_coming_from_the_request_does_not_cascade_back(self):
        video = make_video(additional_data=PUBLISHED_DATA)
        video.request.additional_data = {
            "accepted": True,
            "recording": {"path": "N:/test", "copied_to_gdrive": True},
        }
        video.request.status = Request.Statuses.UPLOADED
        video.request.save()

        update_video_status(video, called_from_request=True)

        video.request.refresh_from_db()
        assert video.request.status == Request.Statuses.UPLOADED
