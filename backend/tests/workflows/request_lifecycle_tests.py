"""The whole journey of a request, from felkérés to lezárva, over the real API.

The individual transition rules are proven one by one in
tests/unit/video_requests/. This is the one place that walks them end to end, so
what it protects is the wiring — the serializers, the status recalculation the
save hooks trigger, and the fact that a video's progress reaches its request.
"""

from datetime import datetime, timedelta
from io import StringIO

import pytest
import time_machine
from django.core.management import call_command
from django.utils.timezone import localtime
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    is_success,
)
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.utils import make_utc

from video_requests.models import Request, Video

pytestmark = pytest.mark.django_db

EVENT_START = "2020-11-21 10:20:30 +0100"
EVENT_END = "2020-11-21 14:30:20 +0100"


@pytest.fixture
def admin_api_client(api_client, admin_user):
    """A client whose token stays valid inside the travelled-to time as well."""
    token = AccessToken.for_user(admin_user)
    token.set_iat(at_time=make_utc(datetime(2020, 11, 21, 0, 0)))
    token.set_exp(lifetime=timedelta(hours=5))
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")
    return api_client


def request_url(request_id=None):
    if request_id is None:
        return reverse("api:v1:admin:requests:request-list")
    return reverse("api:v1:admin:requests:request-detail", kwargs={"pk": request_id})


def video_url(request_id, video_id=None):
    if video_id is None:
        return reverse(
            "api:v1:admin:requests:request:video-list",
            kwargs={"request_pk": request_id},
        )
    return reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": request_id, "pk": video_id},
    )


def patch(client, url, data, expected_status=None):
    """PATCH, assert the HTTP code and optionally the resulting status field."""
    response = client.patch(url, data)
    assert response.status_code == HTTP_200_OK, response.data
    if expected_status is not None:
        assert response.data["status"] == expected_status
    return response.data


def status_of(client, url):
    response = client.get(url)
    assert is_success(response.status_code), response.data
    return response.data["status"]


def test_a_request_walks_from_felkeres_to_lezarva(admin_user, admin_api_client):
    with time_machine.travel(EVENT_START) as traveller:
        response = admin_api_client.post(
            request_url(),
            {
                "title": "Test Request",
                "start_datetime": localtime(),
                "end_datetime": localtime() + timedelta(hours=4),
                "place": "Test place",
                "type": "Test type",
            },
        )
        assert response.status_code == HTTP_201_CREATED
        assert response.data["status"] == Request.Statuses.REQUESTED
        request_id = response.data["id"]
        detail = request_url(request_id)

        # The production manager takes the job on.
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"accepted": True}},
            Request.Statuses.ACCEPTED,
        )

        # The event happens. The nightly command notices it is over.
        traveller.move_to(EVENT_END)
        with StringIO() as out:
            call_command("update_request_status", stdout=out)
            assert out.getvalue() == "1 requests was checked for valid status.\n"
        assert status_of(admin_api_client, detail) == Request.Statuses.RECORDED

        # The raw material lands on the storage server.
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"recording": {"path": "N:/20201121_test"}}},
            Request.Statuses.UPLOADED,
        )

        # A video is cut out of it.
        response = admin_api_client.post(video_url(request_id), {"title": "New video"})
        assert response.status_code == HTTP_201_CREATED
        assert response.data["status"] == Video.Statuses.PENDING
        video_id = response.data["id"]
        video_detail = video_url(request_id, video_id)

        patch(
            admin_api_client,
            video_detail,
            {"editor": admin_user.id},
            Video.Statuses.IN_PROGRESS,
        )
        patch(
            admin_api_client,
            video_detail,
            {"additional_data": {"editing_done": True}},
            Video.Statuses.EDITED,
        )
        # Finishing the only video moves the request with it.
        assert status_of(admin_api_client, detail) == Request.Statuses.EDITED

        # Publishing: raw material to Drive, then encode, publish and archive.
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"recording": {"copied_to_gdrive": True}}},
        )
        patch(
            admin_api_client,
            video_detail,
            {"additional_data": {"coding": {"website": True}}},
            Video.Statuses.CODED,
        )
        patch(
            admin_api_client,
            video_detail,
            {"additional_data": {"publishing": {"website": "https://example.com"}}},
            Video.Statuses.PUBLISHED,
        )
        patch(
            admin_api_client,
            video_detail,
            {"additional_data": {"archiving": {"hq_archive": True}}},
            Video.Statuses.DONE,
        )
        assert status_of(admin_api_client, detail) == Request.Statuses.ARCHIVED

        # Raw files removed: the request is closed.
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"recording": {"removed": True}}},
            Request.Statuses.DONE,
        )

        # Deleting the video walks the request back to where its videos left it.
        response = admin_api_client.delete(video_detail)
        assert response.status_code == HTTP_204_NO_CONTENT
        assert status_of(admin_api_client, detail) == Request.Statuses.UPLOADED

        # The three ways a request can end badly, each reversible.
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"canceled": True}},
            Request.Statuses.CANCELED,
        )
        admin_api_client.patch(detail, {"additional_data": {"canceled": False}})
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"failed": True}},
            Request.Statuses.FAILED,
        )
        patch(
            admin_api_client,
            detail,
            {"additional_data": {"accepted": False}},
            Request.Statuses.DENIED,
        )


def test_an_admin_can_force_the_status_of_a_request_and_its_video(
    admin_user, admin_api_client
):
    response = admin_api_client.post(
        request_url(),
        {
            "title": "Test Request",
            "start_datetime": localtime(),
            "end_datetime": localtime() + timedelta(hours=4),
            "place": "Test place",
            "type": "Test type",
        },
    )
    assert response.status_code == HTTP_201_CREATED
    assert response.data["status"] == Request.Statuses.REQUESTED
    request_id = response.data["id"]

    forced = patch(
        admin_api_client,
        request_url(request_id),
        {
            "additional_data": {
                "status_by_admin": {
                    "status": Request.Statuses.ARCHIVED,
                    # Whoever sent these does not get to choose them.
                    "admin_id": 123,
                    "admin_name": "Random Name",
                }
            }
        },
        Request.Statuses.ARCHIVED,
    )
    assert forced["additional_data"]["status_by_admin"]["admin_id"] == admin_user.id
    assert (
        forced["additional_data"]["status_by_admin"]["admin_name"]
        == admin_user.get_full_name_eastern_order()
    )

    response = admin_api_client.post(video_url(request_id), {"title": "New video"})
    assert response.status_code == HTTP_201_CREATED
    assert response.data["status"] == Video.Statuses.PENDING
    video_id = response.data["id"]

    forced_video = patch(
        admin_api_client,
        video_url(request_id, video_id),
        {
            "additional_data": {
                "status_by_admin": {
                    "status": Video.Statuses.DONE,
                    "admin_id": 123,
                    "admin_name": "Random Name",
                }
            }
        },
        Video.Statuses.DONE,
    )
    assert (
        forced_video["additional_data"]["status_by_admin"]["admin_id"] == admin_user.id
    )
    assert (
        forced_video["additional_data"]["status_by_admin"]["admin_name"]
        == admin_user.get_full_name_eastern_order()
    )

    # A forced request status outlives everything its videos do.
    assert (
        status_of(admin_api_client, request_url(request_id))
        == Request.Statuses.ARCHIVED
    )
