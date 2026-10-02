from random import randint

import pytest
from django.utils.timezone import localtime
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    is_success,
)

from tests.api.asserts import assert_exact_fields
from tests.api.helpers import do_login
from tests.api.matrix import any_user
from video_requests.models import Video

pytestmark = pytest.mark.django_db


def assert_response_keys(video):
    assert_exact_fields(video, ["id", "rating", "status", "title", "video_url"])

    rating = video["rating"]
    if rating:
        assert_exact_fields(rating, ["created", "rating", "review"])


@any_user(HTTP_200_OK)
def test_list_videos_own_request(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    videos = baker.make("video_requests.Video", request=video_request, _quantity=5)

    url = reverse(
        "api:v1:requests:request:video-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(videos)
        for video in response.data:
            assert_response_keys(video)


@any_user(HTTP_404_NOT_FOUND)
def test_list_videos_errors(
    api_client, expected, not_existing_request_id, request, user
):
    video_request = baker.make("video_requests.Request")
    do_login(api_client, request, user)

    # A request where the requester is not the user logged in
    url = reverse(
        "api:v1:requests:request:video-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    # Not existing request
    url = reverse(
        "api:v1:requests:request:video-list",
        kwargs={"request_pk": not_existing_request_id},
    )
    response = api_client.get(url)

    assert response.status_code == expected


@any_user(HTTP_200_OK)
def test_retrieve_video(api_client, expected, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    videos = baker.make("video_requests.Video", request=video_request, _quantity=5)

    url = reverse(
        "api:v1:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": videos[0].id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_response_keys(response.data)


@any_user(HTTP_404_NOT_FOUND)
def test_retrieve_video_errors(
    api_client, expected, not_existing_request_id, not_existing_video_id, request, user
):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request")
    video_request_own = baker.make("video_requests.Request", requester=user)
    video = baker.make("video_requests.Video", request=video_request)
    video_own_request = baker.make("video_requests.Video", request=video_request_own)

    for request_id in [video_request.id, video_request_own.id, not_existing_request_id]:
        for video_id in [video.id, video_own_request.id, not_existing_video_id]:
            if request_id == video_request_own.id and video_id == video_own_request.id:
                continue

            url = reverse(
                "api:v1:requests:request:video-detail",
                kwargs={"request_pk": request_id, "pk": video_id},
            )
            response = api_client.get(url)

            assert response.status_code == expected


@pytest.mark.parametrize(
    "user",
    ["admin_user", "staff_user", "basic_user"],
)
def test_retrieve_video_url(api_client, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    video = baker.make(
        "video_requests.Video",
        additional_data={"publishing": {"website": "https://example.com"}},
        request=video_request,
        status=Video.Statuses.PENDING,
    )

    url = reverse(
        "api:v1:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video.id},
    )

    # Check if it works for all statuses
    for status in Video.Statuses:
        # Change status
        video.status = status
        video.save()

        # Get video details and check if video_url is present as key
        response = api_client.get(url)

        assert response.status_code == HTTP_200_OK
        assert_response_keys(response.data)

        # If status is below 5 no url should be visible
        if status >= Video.Statuses.PUBLISHED:
            assert response.data["video_url"] == "https://example.com"
        else:
            assert not response.data["video_url"]


@pytest.mark.parametrize(
    "user",
    ["admin_user", "staff_user", "basic_user"],
)
def test_retrieve_video_rating(api_client, request, user):
    user = do_login(api_client, request, user)

    video_request = baker.make("video_requests.Request", requester=user)
    video = baker.make("video_requests.Video", request=video_request)

    baker.make("video_requests.Rating", rating=randint(1, 5), video=video, _quantity=5)
    rating_own = baker.make(
        "video_requests.Rating",
        author=user,
        rating=randint(1, 5),
        video=video,
        _fill_optional=["review"],
    )

    url = reverse(
        "api:v1:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video.id},
    )

    response = api_client.get(url)

    assert response.status_code == HTTP_200_OK
    assert_response_keys(response.data)

    assert (
        response.data["rating"]["created"] == localtime(rating_own.created).isoformat()
    )
    assert response.data["rating"]["rating"] == rating_own.rating
    assert response.data["rating"]["review"] == rating_own.review
