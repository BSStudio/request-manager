import json

import pytest
import requests
import responses
from model_bakery import baker

from tests.factories import make_user
from video_requests.mattermost import (
    get_video_published_message,
    post_video_published_to_mattermost,
)

pytestmark = pytest.mark.django_db

WEBHOOK_URL = "https://mattermost.example.com/hooks/test"


@pytest.fixture
def video():
    return baker.make(
        "video_requests.Video",
        title="Egyetemi Napok – Riportok",
        additional_data={"publishing": {"website": "https://example.com/video"}},
    )


def add_crew_member(video, position, last_name, first_name):
    baker.make(
        "video_requests.CrewMember",
        request=video.request,
        member=make_user(first_name=first_name, last_name=last_name),
        position=position,
    )


class TestMessage:
    def test_credits_the_editor_then_the_crew_by_position(self, video):
        video.editor = make_user(first_name="Benedek", last_name="Dobronyi")
        video.save()
        add_crew_member(video, "Riporter", "Kiss", "Péter")
        add_crew_member(video, "Operatőr", "Zsoldos", "Zoé")
        add_crew_member(video, "Operatőr", "Kiss", "Péter")
        add_crew_member(video, "Operatőr", "Ábrahám", "Anna")

        assert get_video_published_message(video) == (
            "#### :clapper: Egyetemi Napok – Riportok\n"
            f"[Videó](https://example.com/video) | [Értékelés a felkéréskezelőben]({video.admin_url})\n"
            "\n"
            "**Vágó:** Dobronyi Benedek\n"
            "**Operatőr:** Ábrahám Anna, Kiss Péter, Zsoldos Zoé\n"
            "**Riporter:** Kiss Péter"
        )

    def test_leaves_out_the_credits_when_there_are_none(self, video):
        assert get_video_published_message(video) == (
            "#### :clapper: Egyetemi Napok – Riportok\n"
            f"[Videó](https://example.com/video) | [Értékelés a felkéréskezelőben]({video.admin_url})"
        )


class TestPost:
    @pytest.fixture
    def mattermost(self, settings):
        settings.MATTERMOST_WEBHOOK_URL = WEBHOOK_URL
        with responses.RequestsMock() as mock:
            yield mock

    def test_marks_the_video_as_posted(self, mattermost, video):
        webhook = mattermost.post(WEBHOOK_URL)

        post_video_published_to_mattermost(video.id)

        assert json.loads(webhook.calls[0].request.body) == {
            "text": get_video_published_message(video)
        }
        video.refresh_from_db()
        assert video.additional_data["publishing"]["posted_on_mattermost"] is True

    def test_a_failed_post_leaves_the_video_unposted(self, mattermost, video):
        mattermost.post(WEBHOOK_URL, status=500)

        with pytest.raises(requests.HTTPError):
            post_video_published_to_mattermost(video.id)

        video.refresh_from_db()
        assert "posted_on_mattermost" not in video.additional_data["publishing"]
