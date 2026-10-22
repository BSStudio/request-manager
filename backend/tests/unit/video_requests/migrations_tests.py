from importlib import import_module

import pytest
from django.apps import apps
from model_bakery import baker

from video_requests.models import Video

pytestmark = pytest.mark.django_db

mark_sent_notifications = import_module(
    "video_requests.migrations.0015_mark_sent_notifications"
).mark_sent_notifications


def test_old_acceptances_and_published_videos_are_marked_as_notified():
    accepted = baker.make("video_requests.Request", additional_data={"accepted": True})
    denied = baker.make("video_requests.Request", additional_data={"accepted": False})
    published = baker.make(
        "video_requests.Video", status=Video.Statuses.PUBLISHED, additional_data={}
    )
    done = baker.make(
        "video_requests.Video",
        status=Video.Statuses.DONE,
        additional_data={"publishing": {"website": "https://example.com"}},
    )
    coded = baker.make(
        "video_requests.Video", status=Video.Statuses.CODED, additional_data={}
    )

    mark_sent_notifications(apps, None)

    for row in (accepted, denied, published, done, coded):
        row.refresh_from_db()
    assert accepted.additional_data["accepted_notification_sent"] is True
    assert "accepted_notification_sent" not in denied.additional_data
    assert published.additional_data["publishing"] == {
        "notification_sent_to_user": True
    }
    assert done.additional_data["publishing"] == {
        "website": "https://example.com",
        "notification_sent_to_user": True,
    }
    assert "publishing" not in coded.additional_data
