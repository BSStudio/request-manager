"""Ordering and searching a requester's own request list."""

from datetime import date, datetime, timedelta

import pytest
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    is_success,
)

from tests.api.helpers import login
from video_requests.models import Request

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [2, 4, 3, 1]),
        ("start_datetime", [4, 2, 3, 1]),
        ("status", [3, 4, 2, 1]),
        ("title", [2, 4, 1, 3]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_requests(
    api_client, basic_user, expected, ordering, pagination, time_machine
):
    requests = []

    start_date = make_aware(
        datetime.combine(date.fromisoformat("2023-05-30"), datetime.min.time())
    )

    time_machine.move_to(datetime(2019, 6, 4))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=4),
            status=Request.Statuses.CANCELED,
            title="CCCC",
        )
    )

    time_machine.move_to(datetime(1990, 8, 7))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=10),
            status=Request.Statuses.DONE,
            title="AAAA",
        )
    )

    time_machine.move_to(datetime(2009, 8, 22))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=8),
            status=Request.Statuses.ACCEPTED,
            title="DDDD",
        )
    )

    time_machine.move_to(datetime(1995, 10, 26))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date,
            requester=basic_user,
            start_datetime=start_date - timedelta(days=15),
            status=Request.Statuses.UPLOADED,
            title="BBBB",
        )
    )

    login(api_client, basic_user)

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(requests):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == requests[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_requests(api_client, basic_user, pagination):
    requests = [
        baker.make(
            "video_requests.Request", requester=basic_user, title="AAAA BBBB CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBBB AAAA CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="CCCC BBBB AAAA"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBCC CCAA AABB"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBBB CCCC BBBB"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBBB BBBB BBBB"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="CCCC CCCC CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="CCCC BBBB CCCC"
        ),
        baker.make(
            "video_requests.Request", requester=basic_user, title="BBAA CCAA AACC"
        ),
    ]

    baker.make("video_requests.Video", request=requests[6], title="AAAA BBBB"),
    baker.make("video_requests.Video", request=requests[7], title="CCCC AAAA"),

    login(api_client, basic_user)

    url = reverse("api:v1:requests:request-list")
    response = api_client.get(url, {"pagination": pagination, "search": "AAAA"})

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 5

    assert response_data[0]["id"] == requests[0].id
    assert response_data[1]["id"] == requests[1].id
    assert response_data[2]["id"] == requests[2].id
    assert response_data[3]["id"] == requests[6].id
    assert response_data[4]["id"] == requests[7].id
