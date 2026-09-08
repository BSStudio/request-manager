"""Filtering, ordering and searching the cross-request video list."""

from datetime import date, datetime, timedelta

import pytest
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from tests.api.helpers import login
from video_requests.models import Video

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"last_aired": "2023-05-01"}, 5),
        ({"length_max": 60}, 4),
        ({"length_min": 60}, 3),
        (
            {
                "length_max": 100,
                "length_min": 60,
            },
            2,
        ),
        ({"request_start_datetime_after": "2021-11-13"}, 3),
        ({"request_start_datetime_before": "2021-11-15"}, 5),
        (
            {
                "request_start_datetime_after": "2021-11-13",
                "request_start_datetime_before": "2021-11-15",
            },
            2,
        ),
        ({"status": Video.Statuses.EDITED}, 1),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_filter_all_videos(admin_user, api_client, filters, expected, pagination):
    start_datetime = make_aware(
        datetime.combine(date.fromisoformat("2021-11-21"), datetime.min.time())
    )

    video_requests = [
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=15)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=1)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=21)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=7)
        ),
    ]

    baker.make(
        "video_requests.Video",
        additional_data={"length": 600},
        request=video_requests[2],
        status=Video.Statuses.PENDING,
        title="AAAA1",
    ),
    baker.make(
        "video_requests.Video",
        additional_data={"aired": ["2023-04-01"]},
        request=video_requests[3],
        status=Video.Statuses.CODED,
        title="BBBB1",
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[0],
        status=Video.Statuses.EDITED,
        title="CCCC1",
    ),
    baker.make(
        "video_requests.Video",
        additional_data={"aired": ["2023-01-21", "2012-01-10"], "length": 60},
        request=video_requests[1],
        status=Video.Statuses.DONE,
        title="BBBB2",
    ),
    baker.make(
        "video_requests.Video",
        additional_data={
            "aired": ["2023-05-30", "2012-01-10", "2008-11-25"],
            "length": 100,
        },
        request=video_requests[0],
        status=Video.Statuses.PUBLISHED,
        title="CCCC2",
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[3],
        status=Video.Statuses.IN_PROGRESS,
        title="AAAA2",
    ),

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(url, {"pagination": pagination} | filters)

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == expected


@pytest.mark.parametrize("pagination", [True, False])
def test_filter_all_videos_multiple_status(admin_user, api_client, pagination):
    video_requests = baker.make("video_requests.Request", _quantity=4)

    baker.make(
        "video_requests.Video", request=video_requests[1], status=Video.Statuses.PENDING
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[3],
        status=Video.Statuses.PUBLISHED,
    ),
    baker.make(
        "video_requests.Video", request=video_requests[1], status=Video.Statuses.DONE
    ),
    baker.make(
        "video_requests.Video",
        request=video_requests[2],
        status=Video.Statuses.IN_PROGRESS,
    ),
    baker.make(
        "video_requests.Video", request=video_requests[2], status=Video.Statuses.EDITED
    ),
    baker.make(
        "video_requests.Video", request=video_requests[0], status=Video.Statuses.CODED
    ),

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(
        url
        + f"?pagination={pagination}&status={Video.Statuses.CODED}&status={Video.Statuses.PUBLISHED}"
    )

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 2


@pytest.mark.parametrize(
    "ordering,expected",
    [
        # Add title as secondary ordering field to make tests consistent.
        ("avg_rating,title", [6, 3, 2, 1, 4, 5]),
        ("last_aired,title", [6, 4, 1, 2, 3, 5]),
        ("length,title", [6, 1, 3, 2, 4, 5]),
        ("request__start_datetime,title", [4, 6, 2, 1, 3, 5]),
        ("status", [2, 6, 5, 3, 1, 4]),
        ("title", [1, 6, 2, 4, 3, 5]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_all_videos(admin_user, api_client, expected, ordering, pagination):
    start_datetime = make_aware(
        datetime.combine(date.fromisoformat("2023-05-30"), datetime.min.time())
    )

    video_request = [
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=1)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=8)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=3)
        ),
        baker.make(
            "video_requests.Request", start_datetime=start_datetime - timedelta(days=7)
        ),
    ]

    videos = [
        baker.make(
            "video_requests.Video",
            additional_data={
                "aired": ["2023-05-30", "2012-01-10", "2008-11-25"],
                "length": 100,
            },
            request=video_request[2],
            status=Video.Statuses.PUBLISHED,
            title="AAAA1",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request[3],
            status=Video.Statuses.PENDING,
            title="BBBB1",
        ),
        baker.make(
            "video_requests.Video",
            additional_data={"length": 600},
            request=video_request[0],
            status=Video.Statuses.CODED,
            title="CCCC1",
        ),
        baker.make(
            "video_requests.Video",
            additional_data={"aired": ["2023-04-01"]},
            request=video_request[1],
            status=Video.Statuses.DONE,
            title="BBBB2",
        ),
        baker.make(
            "video_requests.Video",
            request=video_request[0],
            status=Video.Statuses.EDITED,
            title="CCCC2",
        ),
        baker.make(
            "video_requests.Video",
            additional_data={"aired": ["2023-01-21", "2012-01-10"], "length": 60},
            request=video_request[3],
            status=Video.Statuses.IN_PROGRESS,
            title="AAAA2",
        ),
    ]

    # Avg rating: 4,3 (Video 2)
    baker.make("video_requests.Rating", rating=5, video=videos[1])
    baker.make("video_requests.Rating", rating=5, video=videos[1])
    baker.make("video_requests.Rating", rating=3, video=videos[1])

    # Avg rating: 4 (Video 3)
    baker.make("video_requests.Rating", rating=4, video=videos[2])
    baker.make("video_requests.Rating", rating=4, video=videos[2])
    baker.make("video_requests.Rating", rating=4, video=videos[2])

    # Avg rating: 2,3 (Video 6)
    baker.make("video_requests.Rating", rating=2, video=videos[5])
    baker.make("video_requests.Rating", rating=2, video=videos[5])
    baker.make("video_requests.Rating", rating=3, video=videos[5])

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(videos):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == videos[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_all_videos(admin_user, api_client, pagination):
    video_requests = baker.make("video_requests.Request", _quantity=4)

    videos = [
        baker.make(
            "video_requests.Video", request=video_requests[0], title="AAAA BBBB CCCC"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[2], title="BBBB CCCC BBBB"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[0], title="BBCC CCAA AABB"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[3], title="BBBB AAAA CCCC"
        ),
        baker.make(
            "video_requests.Video", request=video_requests[1], title="CCCC BBBB AAAA"
        ),
    ]

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(
        url, {"ordering": "title", "pagination": pagination, "search": "AAAA"}
    )

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 3

    assert response_data[0]["id"] == videos[0].id
    assert response_data[1]["id"] == videos[3].id
    assert response_data[2]["id"] == videos[4].id
