"""Filtering, ordering and searching the admin request list."""

from datetime import date, datetime, timedelta

import pytest
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import is_success

from common.models import User
from tests.api.helpers import login
from video_requests.models import Request

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"deadline_after": "2003-08-25"}, 5),
        ({"deadline_before": "2009-10-03"}, 3),
        (
            {
                "deadline_after": "2008-03-02",
                "deadline_before": "2015-04-05",
            },
            3,
        ),
        ({"start_datetime_after": "2007-08-25"}, 4),
        ({"start_datetime_before": "2012-01-01"}, 4),
        (
            {
                "start_datetime_after": "2005-01-01",
                "start_datetime_before": "2012-01-01",
            },
            2,
        ),
        ({"status": Request.Statuses.REQUESTED}, 1),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_filter_requests(admin_user, api_client, filters, expected, pagination):
    values = [
        ("1993-10-29", Request.Statuses.CANCELED),
        ("2004-12-10", Request.Statuses.DONE),
        ("2008-03-02", Request.Statuses.UPLOADED),
        ("2009-10-03", Request.Statuses.REQUESTED),
        ("2015-03-12", Request.Statuses.EDITED),
        ("2022-11-25", Request.Statuses.DENIED),
    ]

    requests = []

    for start_date, status in values:
        start_datetime = make_aware(
            datetime.combine(date.fromisoformat(start_date), datetime.min.time())
        )
        end_datetime = start_datetime + timedelta(hours=3)
        requests.append(
            baker.make(
                "video_requests.Request",
                end_datetime=end_datetime,
                status=status,
                start_datetime=start_datetime,
            )
        )

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, {"pagination": pagination} | filters)

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == expected


@pytest.mark.parametrize("pagination", [True, False])
def test_filter_requests_multiple_status(admin_user, api_client, pagination):
    baker.make("video_requests.Request", status=Request.Statuses.UPLOADED),
    baker.make("video_requests.Request", status=Request.Statuses.ACCEPTED),
    baker.make("video_requests.Request", status=Request.Statuses.ARCHIVED),
    baker.make("video_requests.Request", status=Request.Statuses.FAILED),
    baker.make("video_requests.Request", status=Request.Statuses.RECORDED),
    baker.make("video_requests.Request", status=Request.Statuses.CANCELED),

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(
        url
        + f"?pagination={pagination}&status={Request.Statuses.RECORDED}&status={Request.Statuses.ACCEPTED}"
    )

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 2


@pytest.mark.parametrize(
    "ordering,expected",
    [
        ("created", [6, 2, 3, 1, 5, 4]),
        ("deadline", [4, 6, 2, 3, 1, 5]),
        # There can be a difference in ordering of similar object if pagination is enabled.
        # Add created as secondary ordering field to make tests consistent.
        ("responsible__first_name,created", [6, 2, 5, 3, 1, 4]),
        ("responsible__last_name,created", [6, 3, 5, 2, 1, 4]),
        ("responsible__last_name,responsible__first_name,created", [6, 5, 3, 2, 1, 4]),
        ("start_datetime", [4, 6, 2, 3, 1, 5]),
        ("status", [3, 6, 2, 4, 1, 5]),
        ("title", [2, 4, 1, 3, 6, 5]),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_order_requests(
    admin_user, api_client, expected, ordering, pagination, time_machine
):
    test_responsible_1 = baker.make(User, first_name="AAAA", last_name="CCCC")
    test_responsible_2 = baker.make(User, first_name="CCCC", last_name="BBBB")
    test_responsible_3 = baker.make(User, first_name="AAAA", last_name="BBBB")

    requests = []

    start_date = make_aware(
        datetime.combine(date.fromisoformat("2023-05-30"), datetime.min.time())
    )

    time_machine.move_to(datetime(2006, 3, 16))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=3),
            start_datetime=start_date - timedelta(days=4),
            status=Request.Statuses.DONE,
            title="CCCC",
        )
    )

    time_machine.move_to(datetime(1999, 6, 14))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=9),
            responsible=test_responsible_1,
            start_datetime=start_date - timedelta(days=10),
            status=Request.Statuses.RECORDED,
            title="AAAA",
        )
    )

    time_machine.move_to(datetime(2003, 12, 17))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=7),
            responsible=test_responsible_2,
            start_datetime=start_date - timedelta(days=8),
            status=Request.Statuses.DENIED,
            title="DDDD",
        )
    )

    time_machine.move_to(datetime(2023, 6, 16))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=14),
            start_datetime=start_date - timedelta(days=15),
            status=Request.Statuses.UPLOADED,
            title="BBBB",
        )
    )

    time_machine.move_to(datetime(2020, 12, 25))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=1),
            responsible=test_responsible_3,
            start_datetime=start_date - timedelta(days=2),
            status=Request.Statuses.CANCELED,
            title="FFFF",
        )
    )

    time_machine.move_to(datetime(1999, 2, 8))
    requests.append(
        baker.make(
            "video_requests.Request",
            end_datetime=start_date - timedelta(days=12),
            responsible=test_responsible_3,
            start_datetime=start_date - timedelta(days=13),
            status=Request.Statuses.ACCEPTED,
            title="EEEE",
        )
    )

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, {"ordering": ordering, "pagination": pagination})

    assert is_success(response.status_code)

    for i, _ in enumerate(requests):
        response_data = response.data["results"] if pagination else response.data

        assert response_data[i]["id"] == requests[expected[i] - 1].id


@pytest.mark.parametrize("pagination", [True, False])
def test_search_requests(admin_user, api_client, pagination):
    requests = [
        baker.make("video_requests.Request", title="AAAA BBBB CCCC"),
        baker.make("video_requests.Request", title="BBBB AAAA CCCC"),
        baker.make("video_requests.Request", title="CCCC BBBB AAAA"),
        baker.make("video_requests.Request", title="BBCC CCAA AABB"),
        baker.make("video_requests.Request", title="BBBB CCCC BBBB"),
    ]

    login(api_client, admin_user)

    url = reverse("api:v1:admin:requests:request-list")
    response = api_client.get(url, {"pagination": pagination, "search": "AAAA"})

    assert is_success(response.status_code)

    response_data = response.data["results"] if pagination else response.data

    assert len(response_data) == 3

    assert response_data[0]["id"] == requests[0].id
    assert response_data[1]["id"] == requests[1].id
    assert response_data[2]["id"] == requests[2].id
