from random import randint

import pytest
from model_bakery import baker
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    is_client_error,
    is_success,
)

from common.models import User
from tests.api.helpers import assert_fields_exist, do_login, get_response
from video_requests.models import Video

pytestmark = pytest.mark.django_db


def assert_list_response_keys(video):
    assert_fields_exist(
        video,
        ["avg_rating", "editor", "id", "rated", "status", "status_by_admin", "title"],
    )

    editor = video.get("editor")
    if editor:
        assert_fields_exist(editor, ["avatar_url", "full_name", "id"])


def assert_retrieve_response_keys(video):
    assert_fields_exist(
        video,
        [
            "additional_data",
            "avg_rating",
            "editor",
            "id",
            "rated",
            "status",
            "status_by_admin",
            "title",
        ],
    )

    editor = video.get("editor")
    if editor:
        assert_fields_exist(editor, ["avatar_url", "full_name", "id"])


@pytest.fixture
def video_data():
    return {"title": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_list_videos(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    videos = baker.make("video_requests.Video", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert len(response.data) == len(videos)
        for video in response.data:
            assert_list_response_keys(video)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_201_CREATED),
        ("staff_user", HTTP_201_CREATED),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_create_video(api_client, expected, request, user, video_data):
    video_request = baker.make("video_requests.Request")

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video-list",
        kwargs={"request_pk": video_request.id},
    )
    response = api_client.post(url, video_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)

        response = api_client.get(url)

        assert response.status_code == HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_list_create_videos_error(
    api_client, expected, method, not_existing_request_id, request, user, video_data
):
    video_request = baker.make("video_requests.Request")
    baker.make("video_requests.Video", request=video_request, _quantity=5)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video-list",
        kwargs={"request_pk": not_existing_request_id},
    )

    response = get_response(api_client, method, url, video_data)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", {"DELETE": HTTP_204_NO_CONTENT, "GET": HTTP_200_OK}),
        ("staff_user", {"DELETE": HTTP_204_NO_CONTENT, "GET": HTTP_200_OK}),
        ("basic_user", {"DELETE": HTTP_403_FORBIDDEN, "GET": HTTP_403_FORBIDDEN}),
        ("service_account", {"DELETE": HTTP_403_FORBIDDEN, "GET": HTTP_403_FORBIDDEN}),
        (None, {"DELETE": HTTP_401_UNAUTHORIZED, "GET": HTTP_401_UNAUTHORIZED}),
    ],
)
@pytest.mark.parametrize("method", ["DELETE", "GET"])
def test_retrieve_destroy_video(api_client, expected, method, request, user):
    video_request = baker.make("video_requests.Request")
    videos = baker.make("video_requests.Video", request=video_request, _quantity=5)
    ratings = baker.make(
        "video_requests.Rating", rating=randint(1, 5), video=videos[0], _quantity=5
    )

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": videos[0].id},
    )
    response = get_response(api_client, method, url, None)

    assert response.status_code == expected[method]

    if is_success(response.status_code) and method == "GET":
        assert_retrieve_response_keys(response.data)
        assert response.data["avg_rating"] == sum(
            rating.rating for rating in ratings
        ) / len(ratings)


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_video_status_by_admin(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video_1 = baker.make(
        "video_requests.Video", additional_data={}, request=video_request
    )
    video_2 = baker.make(
        "video_requests.Video",
        additional_data={
            "status_by_admin": {"status": 5, "admin_id": 1, "admin_name": "Test Admin"}
        },
        request=video_request,
    )

    do_login(api_client, request, user)

    url_1 = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video_1.id},
    )
    url_2 = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video_2.id},
    )

    response_1 = api_client.get(url_1)
    response_2 = api_client.get(url_2)

    assert response_1.status_code == expected
    assert response_2.status_code == expected

    if is_success(response_1.status_code) and is_success(response_2.status_code):
        assert_retrieve_response_keys(response_1.data)
        assert_retrieve_response_keys(response_2.data)

        assert not response_1.data.get("status_by_admin")
        assert response_2.data.get("status_by_admin")


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
def test_retrieve_video_rated(api_client, expected, request, user):
    video_request = baker.make("video_requests.Request")
    video = baker.make(
        "video_requests.Video", request=video_request, status=Video.Statuses.EDITED
    )

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video.id},
    )

    # Check video without rating --> Rated should be False

    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert response.data.get("rated") is False

    # Create a rating
    url_rating = reverse(
        "api:v1:admin:requests:request:video:rating-list",
        kwargs={"request_pk": video_request.id, "video_pk": video.id},
    )
    response = api_client.post(url_rating, {"rating": 5})

    if is_client_error(expected):
        assert response.status_code == expected
    else:
        assert is_success(response.status_code)

    # Check if rated is True now
    response = api_client.get(url)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert response.data.get("rated") is True


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_video(api_client, expected, method, request, user, video_data):
    video_request = baker.make("video_requests.Request")
    video = baker.make("video_requests.Video", request=video_request)

    do_login(api_client, request, user)

    assert video.title != video_data["title"]

    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video.id},
    )

    response = get_response(api_client, method, url, video_data)

    assert response.status_code == expected

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)
        assert response.data["title"] == video_data["title"]


@pytest.mark.parametrize(
    "user,expected",
    [
        (
            "admin_user",
            {"PATCH": HTTP_200_OK, "POST": HTTP_201_CREATED, "PUT": HTTP_200_OK},
        ),
        (
            "staff_user",
            {"PATCH": HTTP_200_OK, "POST": HTTP_201_CREATED, "PUT": HTTP_200_OK},
        ),
        (
            "basic_user",
            {
                "PATCH": HTTP_403_FORBIDDEN,
                "POST": HTTP_403_FORBIDDEN,
                "PUT": HTTP_403_FORBIDDEN,
            },
        ),
        (
            "service_account",
            {
                "PATCH": HTTP_403_FORBIDDEN,
                "POST": HTTP_403_FORBIDDEN,
                "PUT": HTTP_403_FORBIDDEN,
            },
        ),
        (
            None,
            {
                "PATCH": HTTP_401_UNAUTHORIZED,
                "POST": HTTP_401_UNAUTHORIZED,
                "PUT": HTTP_401_UNAUTHORIZED,
            },
        ),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "POST", "PUT"])
def test_create_update_video_editor(
    api_client, expected, method, request, user, video_data
):
    video_request = baker.make("video_requests.Request")
    test_user = baker.make(User, is_staff=True, _fill_optional=["email"])

    do_login(api_client, request, user)

    if method == "POST":
        url = reverse(
            "api:v1:admin:requests:request:video-list",
            kwargs={"request_pk": video_request.id},
        )
    else:
        video = baker.make("video_requests.Video", request=video_request)
        url = reverse(
            "api:v1:admin:requests:request:video-detail",
            kwargs={"request_pk": video_request.id, "pk": video.id},
        )

    response = get_response(
        api_client, method, url, video_data | {"editor": test_user.id}
    )

    assert response.status_code == expected[method]

    if is_success(response.status_code):
        assert_retrieve_response_keys(response.data)

        assert response.data["editor"]["avatar_url"] == test_user.userprofile.avatar_url
        assert (
            response.data["editor"]["full_name"]
            == test_user.get_full_name_eastern_order()
        )
        assert response.data["editor"]["id"] == test_user.id


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_update_video_remove_editor(
    api_client, expected, method, request, user, video_data
):
    video_request = baker.make("video_requests.Request")
    test_user = baker.make(User, is_staff=True, _fill_optional=["email"])
    video = baker.make("video_requests.Video", editor=test_user, request=video_request)

    do_login(api_client, request, user)

    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": video_request.id, "pk": video.id},
    )

    response_before = api_client.get(url)
    response = get_response(api_client, method, url, video_data | {"editor": None})

    assert response.status_code == expected

    if is_success(response.status_code):
        assert response_before.data["editor"]["id"] == test_user.id
        assert not response.data["editor"]


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_404_NOT_FOUND),
        ("staff_user", HTTP_404_NOT_FOUND),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("method", ["GET", "DELETE", "PATCH", "PUT"])
def test_retrieve_update_destroy_video_error(
    api_client, expected, method, not_existing_request_id, request, user, video_data
):
    def get_not_existing_video_id():
        while True:
            non_existing_id = randint(1000, 100000)
            if not Video.objects.filter(pk=non_existing_id).exists():
                return non_existing_id

    video_requests = baker.make("video_requests.Request", _quantity=2)
    video = baker.make("video_requests.Video", request=video_requests[0])

    do_login(api_client, request, user)

    # Existing request with not existing video
    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={
            "request_pk": video_requests[0].id,
            "pk": get_not_existing_video_id(),
        },
    )
    response = get_response(api_client, method, url, video_data)

    assert response.status_code == expected

    # Not existing request with existing video
    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={"request_pk": not_existing_request_id, "pk": video.id},
    )
    response = get_response(api_client, method, url, video_data)

    assert response.status_code == expected

    # Not existing request with not existing video
    url = reverse(
        "api:v1:admin:requests:request:video-detail",
        kwargs={
            "request_pk": not_existing_request_id,
            "pk": get_not_existing_video_id(),
        },
    )
    response = get_response(api_client, method, url, video_data)

    assert response.status_code == expected


"""
--------------------------------------------------
                   ALL VIDEOS
--------------------------------------------------
"""


@pytest.mark.parametrize(
    "user,expected",
    [
        ("admin_user", HTTP_200_OK),
        ("staff_user", HTTP_200_OK),
        ("basic_user", HTTP_403_FORBIDDEN),
        ("service_account", HTTP_403_FORBIDDEN),
        (None, HTTP_401_UNAUTHORIZED),
    ],
)
@pytest.mark.parametrize("pagination", [True, False])
def test_list_all_videos(api_client, expected, pagination, request, user):
    video_requests = baker.make("video_requests.Request", _quantity=5)
    videos = []

    for video_request in video_requests:
        videos.extend(
            baker.make("video_requests.Video", request=video_request, _quantity=2)
        )

    do_login(api_client, request, user)

    url = reverse("api:v1:admin:requests:video-list")
    response = api_client.get(url, {"pagination": pagination})

    assert response.status_code == expected

    if is_success(response.status_code):
        if pagination:
            assert_fields_exist(
                response.data, ["count", "links", "results", "total_pages"]
            )
            assert_fields_exist(response.data["links"], ["next", "previous"])

            assert response.data["count"] == len(videos)

        response_data = response.data["results"] if pagination else response.data

        assert len(response_data) == len(videos)
        for video in response_data:
            assert_fields_exist(
                video,
                [
                    "avg_rating",
                    "editor",
                    "id",
                    "last_aired",
                    "length",
                    "request_id",
                    "request_start_datetime",
                    "status",
                    "status_by_admin",
                    "title",
                ],
            )
