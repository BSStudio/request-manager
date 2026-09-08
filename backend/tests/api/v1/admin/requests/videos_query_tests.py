"""Ordering the videos of one request."""

import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from common.models import User
from tests.api.helpers import login
from video_requests.models import Video

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "ordering,expected",
    [
        # Add title as secondary ordering field to make tests consistent.
        ("avg_rating,title", [1, 5, 4, 6, 2, 3]),
        ("editor__first_name,title", [1, 6, 5, 4, 2, 3]),
        ("editor__last_name,title", [6, 4, 5, 1, 2, 3]),
        ("editor__last_name,editor__first_name,title", [6, 5, 4, 1, 2, 3]),
        ("status", [2, 6, 5, 3, 1, 4]),
        ("title", [1, 6, 2, 4, 3, 5]),
    ],
)
def test_order_videos(admin_user, api_client, expected, ordering):
    video_request = baker.make("video_requests.Request")

    test_editor_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_editor_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_editor_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    videos = [
        baker.make(
            "video_requests.Video",
            editor=test_editor_1,
            request=video_request,
            status=Video.Statuses.PUBLISHED,
            title="AAAA1",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request,
            status=Video.Statuses.PENDING,
            title="BBBB1",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request,
            status=Video.Statuses.CODED,
            title="CCCC1",
        ),
        baker.make(
            "video_requests.Video",
            editor=test_editor_2,
            request=video_request,
            status=Video.Statuses.DONE,
            title="BBBB2",
        ),
        baker.make(
            "video_requests.Video",
            editor=test_editor_3,
            request=video_request,
            status=Video.Statuses.EDITED,
            title="CCCC2",
        ),
        baker.make(
            "video_requests.Video",
            editor=test_editor_3,
            request=video_request,
            status=Video.Statuses.IN_PROGRESS,
            title="AAAA2",
        ),
    ]

    # Avg rating: 2 (Video 1)
    baker.make("video_requests.Rating", rating=1, video=videos[0])
    baker.make("video_requests.Rating", rating=2, video=videos[0])
    baker.make("video_requests.Rating", rating=3, video=videos[0])

    # Avg rating: 3,3 (Video 4)
    baker.make("video_requests.Rating", rating=5, video=videos[3])
    baker.make("video_requests.Rating", rating=2, video=videos[3])
    baker.make("video_requests.Rating", rating=3, video=videos[3])

    # Avg rating: 3 (Video 5)
    baker.make("video_requests.Rating", rating=4, video=videos[4])
    baker.make("video_requests.Rating", rating=4, video=videos[4])
    baker.make("video_requests.Rating", rating=1, video=videos[4])

    login(api_client, admin_user)

    url = reverse(
        "api:v1:admin:requests:request:video-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url, {"ordering": ordering})

    assert is_success(response.status_code)

    for i, _ in enumerate(videos):
        assert response.data[i]["id"] == videos[expected[i] - 1].id
