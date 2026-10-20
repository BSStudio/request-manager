from datetime import date, datetime

import pytest
from django.utils.timezone import make_aware
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from tests.api.helpers import do_login, login
from tests.api.matrix import staff_only
from video_requests.models import Request, Video

pytestmark = pytest.mark.django_db

SEPTEMBER = {"date_after": "2026-09-01", "date_before": "2026-09-30"}
NOT_HAPPENED = [
    Request.Statuses.DENIED,
    Request.Statuses.CANCELED,
    Request.Statuses.FAILED,
]


def get_report(api_client, params):
    return api_client.get(reverse("api:v1:admin:report"), params)


def event(title, start, end, **kwargs):
    return baker.make(
        Request,
        end_datetime=make_aware(end),
        start_datetime=make_aware(start),
        title=title,
        **kwargs,
    )


def cut_video(title, edited_at):
    return baker.make(
        Video,
        additional_data={"editing_done": True},
        edited_at=edited_at,
        status=Video.Statuses.EDITED,
        title=title,
    )


@staff_only(HTTP_200_OK)
def test_report_permissions(api_client, expected, request, user):
    do_login(api_client, request, user)

    assert get_report(api_client, SEPTEMBER).status_code == expected


def test_report_lists_events_running_in_the_period(api_client, staff_user):
    login(api_client, staff_user)
    event("Before", datetime(2026, 8, 20, 18), datetime(2026, 8, 20, 22))
    event("From August", datetime(2026, 8, 31, 18), datetime(2026, 9, 2, 2))
    event("Whole month", datetime(2026, 8, 25, 10), datetime(2026, 10, 5, 10))
    # Already the next day in Budapest, still the day before in UTC.
    event("First night", datetime(2026, 9, 1, 0, 30), datetime(2026, 9, 1, 2))
    event("October night", datetime(2026, 10, 1, 0, 30), datetime(2026, 10, 1, 2))
    event("Into October", datetime(2026, 9, 30, 20), datetime(2026, 10, 1, 1))
    event("After", datetime(2026, 10, 1, 18), datetime(2026, 10, 1, 22))

    response = get_report(api_client, SEPTEMBER)

    assert [(row["title"], row["date"]) for row in response.data["requests"]] == [
        ("Whole month", "2026-08-25"),
        ("From August", "2026-08-31"),
        ("First night", "2026-09-01"),
        ("Into October", "2026-09-30"),
    ]


@pytest.mark.parametrize("status", Request.Statuses)
def test_report_leaves_out_requests_that_did_not_happen(api_client, staff_user, status):
    login(api_client, staff_user)
    event("Event", datetime(2026, 9, 10, 18), datetime(2026, 9, 10, 22), status=status)

    response = get_report(api_client, SEPTEMBER)

    assert len(response.data["requests"]) == (0 if status in NOT_HAPPENED else 1)


def test_report_lists_videos_cut_in_the_period(api_client, staff_user):
    login(api_client, staff_user)
    cut_video("Earlier", date(2026, 8, 31))
    cut_video("Last day", date(2026, 9, 30))
    cut_video("B on the first", date(2026, 9, 1))
    cut_video("A on the first", date(2026, 9, 1))
    cut_video("Later", date(2026, 10, 1))
    baker.make(Video, title="Uncut")

    response = get_report(api_client, SEPTEMBER)

    assert [(row["title"], row["date"]) for row in response.data["videos"]] == [
        ("A on the first", "2026-09-01"),
        ("B on the first", "2026-09-01"),
        ("Last day", "2026-09-30"),
    ]


@pytest.mark.parametrize(
    "params,fields",
    [
        ({}, {"date_after", "date_before"}),
        ({"date_after": "LoremIpsum", "date_before": "2026-09-30"}, {"date_after"}),
        ({"date_after": "2026-09-30", "date_before": "2026-09-01"}, {"date_after"}),
    ],
)
def test_report_needs_a_valid_period(api_client, staff_user, params, fields):
    login(api_client, staff_user)

    response = get_report(api_client, params)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert set(response.data) == fields
