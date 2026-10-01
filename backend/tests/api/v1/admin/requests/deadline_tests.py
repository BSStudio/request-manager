"""The automatic deadline, through the admin serializer.

``recalculate_deadline`` itself is unit tested in
tests/unit/video_requests/deadline_tests.py.
"""

from datetime import timedelta

import pytest
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from tests.api.helpers import login

pytestmark = pytest.mark.django_db

NOW = "2020-11-21 10:20:30 +0100"
NEW_END = "2020-12-31T10:30:00+01:00"
NEW_DEADLINE = "2021-01-21"


@pytest.fixture(autouse=True)
def frozen(time_machine):
    """Fixed dates, so the expected deadlines can be written out in full."""
    time_machine.move_to(NOW)


@pytest.fixture
def video_request(admin_user, api_client, frozen):
    login(api_client, admin_user)
    # A day long, so a test can push start_datetime around inside it.
    return baker.make(
        "video_requests.Request",
        requester=admin_user,
        start_datetime=localtime(),
        end_datetime=localtime() + timedelta(days=1),
    )


def detail_url(video_request):
    return reverse(
        "api:v1:admin:requests:request-detail", kwargs={"pk": video_request.id}
    )


def test_creating_a_request_generates_a_deadline_three_weeks_out(
    admin_user, api_client, frozen
):
    login(api_client, admin_user)
    end = localtime() + timedelta(hours=4)

    response = api_client.post(
        reverse("api:v1:admin:requests:request-list"),
        {
            "title": "Test Request",
            "start_datetime": localtime(),
            "end_datetime": end,
            "place": "Test place",
            "type": "Test type",
        },
    )

    assert response.status_code == HTTP_201_CREATED
    assert response.data["deadline"] == str((end + timedelta(weeks=3)).date())


@pytest.mark.parametrize(
    "body",
    [
        {"end_datetime": NEW_END},
        # The dashboard sends the whole object back, old deadline included.
        {"end_datetime": NEW_END, "deadline": "echo"},
    ],
    ids=["deadline_omitted", "old_deadline_echoed_back"],
)
def test_moving_the_event_moves_an_untouched_deadline(api_client, body, video_request):
    if body.get("deadline") == "echo":
        body = body | {"deadline": video_request.deadline}

    response = api_client.patch(detail_url(video_request), body)

    assert response.status_code == HTTP_200_OK
    assert response.data["deadline"] == NEW_DEADLINE


@pytest.mark.parametrize("send_deadline", [False, True], ids=["omitted", "echoed_back"])
def test_a_hand_picked_deadline_is_never_moved_for_you(
    api_client, send_deadline, video_request
):
    # Somebody moved this deadline off the automatic offset on purpose, so the
    # new end_datetime is simply rejected against it.
    video_request.deadline = (video_request.end_datetime + timedelta(days=5)).date()
    video_request.save()

    body = {"end_datetime": NEW_END}
    if send_deadline:
        body |= {"deadline": video_request.deadline}

    response = api_client.patch(detail_url(video_request), body)

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data["deadline"][0] == "Must be later than the end of the event."


@pytest.mark.parametrize(
    "send_end_datetime", [False, True], ids=["omitted", "unchanged"]
)
def test_leaving_the_end_datetime_alone_leaves_the_deadline_alone(
    api_client, send_end_datetime, video_request
):
    body = {"start_datetime": video_request.start_datetime + timedelta(hours=4)}
    if send_end_datetime:
        body |= {"end_datetime": video_request.end_datetime}

    response = api_client.patch(detail_url(video_request), body)

    assert response.status_code == HTTP_200_OK
    assert response.data["deadline"] == str(video_request.deadline)
